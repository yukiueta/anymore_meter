"""
process_meter を使った統合テスト

30分データ（MeterReading）を作成し、process_meterを呼んで
BillingSummaryが正しく生成されるかを検証する。

テストケース:
1. 正常ケース: 検針日に30分データあり
2. 検針日にデータなし、期間中にデータあり（パターン4）
3. 検針日にも期間中にもデータなし（みなし）
4. 前回検針日にデータなし、今回あり（初回みなし後の実測）
5. 連続みなし後の実測（みなし調整確認）
"""
from decimal import Decimal
from datetime import date, timedelta
import datetime
from django.test import TestCase
from django.utils import timezone
from django.db.models import Sum

from app.meters.models import Meter, MeterAssignment
from app.readings.models import MeterReading
from app.billing.models import BillingCalendar, BillingSummary
from app.billing.tasks import process_meter, get_deemed_daily_kwh


def make_meter(meter_id='TEST001'):
    return Meter.objects.create(meter_id=meter_id, status='active')


def make_assignment(meter, zone=3, base_billing_day='10'):
    return MeterAssignment.objects.create(
        meter=meter,
        project_id=1,
        project_name='テスト案件',
        zone=zone,
        base_billing_day=base_billing_day,
        start_date=date(2026, 1, 1),
    )


def make_30min_readings(meter, target_date, import_kwh_final, export_kwh_final, count=48):
    """
    指定日に30分データをcount件作成する。
    最終レコードがimport_kwh_final, export_kwh_finalになるよう線形に増加させる。
    """
    readings = []
    for i in range(count):
        hour = (i * 30) // 60
        minute = (i * 30) % 60
        ts = timezone.make_aware(
            datetime.datetime.combine(target_date, datetime.time(hour, minute))
        )
        # 線形補間（最終値に向かって増加）
        ratio = Decimal(str((i + 1) / count))
        import_kwh = (import_kwh_final * ratio).quantize(Decimal('0.01'))
        export_kwh = (export_kwh_final * ratio).quantize(Decimal('0.01'))
        readings.append(MeterReading(
            meter=meter,
            timestamp=ts,
            reading_type='interval',
            import_kwh=import_kwh,
            export_kwh=Decimal('0'),
            route_b_import_kwh=Decimal('0'),
            route_b_export_kwh=export_kwh,
        ))
    MeterReading.objects.bulk_create(readings)


class ProcessMeterIntegrationTest(TestCase):

    def setUp(self):
        self.meter = make_meter()
        self.assignment = make_assignment(self.meter)

    # =========================================================
    # ケース1: 正常ケース - 両検針日に30分データあり
    # =========================================================
    def test_case1_both_dates_have_data(self):
        """
        1/10: 発電累積500, 売電累積100（30分データ48件）
        2/10: 発電累積700, 売電累積200（30分データ48件）
        → 自家消費: (700-500)-(200-100) = 100kWh
        """
        make_30min_readings(self.meter, date(2026, 1, 10), Decimal('500'), Decimal('100'))
        make_30min_readings(self.meter, date(2026, 2, 10), Decimal('700'), Decimal('200'))

        created = process_meter(self.assignment, date(2026, 1, 10), date(2026, 2, 10))
        self.assertTrue(created)

        bs = BillingSummary.objects.get(meter=self.meter, period_start=date(2026, 1, 10), period_end=date(2026, 2, 10))
        self.assertEqual(bs.deemed_method, 'none')
        self.assertTrue(bs.is_first_billing)
        self.assertEqual(bs.total_kwh, Decimal('100'))
        self.assertEqual(bs.curr_used_import, Decimal('700'))
        self.assertEqual(bs.curr_used_export, Decimal('200'))

    # =========================================================
    # ケース2: 検針終了日にデータなし、期間中にデータあり（パターン4）
    # =========================================================
    def test_case2_no_end_data_mid_period_data(self):
        """
        1/10: 発電500, 売電100（30分データあり）
        2/10: データなし（検針終了日）
        2/20: 発電600, 売電150（期間中データ）
        → 実測分: (600-500)-(150-100)=50kWh
        → みなし分: (3/10-2/20)=19日×6kWh=114kWh（ただし period_end=2/10なので残日数は2/10-2/20は無効）

        ※ period_end=2/10, mid_actual_date=2/20なので期中データが期間外になる
        → 期間中データは period_start < date < period_end のフィルタ
        → 2/20は2/10〜3/10の期間では期間中だが、period_end=2/10の場合は範囲外
        → このテストは period_end=3/10 で設定する
        """
        make_30min_readings(self.meter, date(2026, 1, 10), Decimal('500'), Decimal('100'))
        # 2/10（検針終了日）はデータなし
        make_30min_readings(self.meter, date(2026, 2, 20), Decimal('600'), Decimal('150'))

        # 1回目: 1/10〜2/10（前回検針日にデータあり、今回なし）
        created1 = process_meter(self.assignment, date(2026, 1, 10), date(2026, 2, 10))
        self.assertTrue(created1)
        bs1 = BillingSummary.objects.get(meter=self.meter, period_start=date(2026, 1, 10), period_end=date(2026, 2, 10))
        # 今回検針日(2/10)にデータなし、期間中(1/10〜2/10)にもなし → みなし
        self.assertEqual(bs1.deemed_method, 'monthly')

        # 2回目: 2/10〜3/10（期間中2/20にデータあり）
        created2 = process_meter(self.assignment, date(2026, 2, 10), date(2026, 3, 10))
        self.assertTrue(created2)
        bs2 = BillingSummary.objects.get(meter=self.meter, period_start=date(2026, 2, 10), period_end=date(2026, 3, 10))
        self.assertEqual(bs2.deemed_method, 'daily')
        self.assertEqual(bs2.mid_actual_date, date(2026, 2, 20))
        # 実測分: (600-0)-(150-0)=450（bs1のcurr_used_import=0から）
        self.assertEqual(bs2.actual_kwh, Decimal('50'))
        remaining_days = (date(2026, 3, 10) - date(2026, 2, 20)).days
        self.assertEqual(bs2.deemed_kwh, Decimal('6.0') * remaining_days)

    # =========================================================
    # ケース3: 検針日にも期間中にもデータなし（みなし）
    # =========================================================
    def test_case3_no_data_at_all(self):
        """
        1/10: データなし
        2/10: データなし
        → みなし: 6×31=186kWh
        """
        created = process_meter(self.assignment, date(2026, 1, 10), date(2026, 2, 10))
        self.assertTrue(created)

        bs = BillingSummary.objects.get(meter=self.meter, period_start=date(2026, 1, 10), period_end=date(2026, 2, 10))
        self.assertEqual(bs.deemed_method, 'monthly')
        self.assertTrue(bs.is_first_billing)
        days = (date(2026, 2, 10) - date(2026, 1, 10)).days
        self.assertEqual(bs.total_kwh, Decimal('6.0') * days)

    # =========================================================
    # ケース4: 前回検針日にデータなし、今回あり（初回みなし後の実測）
    # =========================================================
    def test_case4_first_deemed_then_actual(self):
        """
        1回目(1/10〜2/10): データなし → みなし
          curr_used_import=0, curr_used_export=0
        2回目(2/10〜3/10):
          2/10: データなし（前回検針日のデータも3/10のデータも取る）
          3/10: 発電500, 売電100
          → prev_used_import=0（bs1から）
          → 自家消費: (500-0)-(100-0)=400
        """
        # 1回目: データなし
        created1 = process_meter(self.assignment, date(2026, 1, 10), date(2026, 2, 10))
        self.assertTrue(created1)
        bs1 = BillingSummary.objects.get(meter=self.meter, period_start=date(2026, 1, 10), period_end=date(2026, 2, 10))
        self.assertEqual(bs1.deemed_method, 'monthly')
        self.assertEqual(bs1.curr_used_import, Decimal('0'))
        self.assertEqual(bs1.curr_used_export, Decimal('0'))

        # 2/10にデータなし、3/10にデータあり
        make_30min_readings(self.meter, date(2026, 3, 10), Decimal('500'), Decimal('100'))

        created2 = process_meter(self.assignment, date(2026, 2, 10), date(2026, 3, 10))
        self.assertTrue(created2)
        bs2 = BillingSummary.objects.get(meter=self.meter, period_start=date(2026, 2, 10), period_end=date(2026, 3, 10))
        self.assertEqual(bs2.deemed_method, 'none')
        self.assertEqual(bs2.total_kwh, Decimal('400'))
        self.assertEqual(bs2.curr_used_import, Decimal('500'))
        self.assertEqual(bs2.curr_used_export, Decimal('100'))

    # =========================================================
    # ケース5: 連続みなし後の実測（みなし調整確認）
    # =========================================================
    def test_case5_multiple_deemed_then_actual_adjustment(self):
        """
        1回目(1/10〜2/10): 発電500, 売電100 → 自家消費400
        2回目(2/10〜3/10): データなし → みなし
        3回目(3/10〜4/10): データなし → みなし
        4回目(4/10〜5/10): 発電700, 売電200
          prev_used_import=500（1回目から引き継ぎ）
          自家消費: (700-500)-(200-100)=100
          actual_cumulative=(700-200)-(500-100)=500-400=100
          billed_cumulative=400+みなし2+みなし3+100
          adjustment=100-billed_cumulative（マイナスになるはず）
        """
        make_30min_readings(self.meter, date(2026, 1, 10), Decimal('300'), Decimal('50'))
        make_30min_readings(self.meter, date(2026, 2, 10), Decimal('500'), Decimal('100'))

        created1 = process_meter(self.assignment, date(2026, 1, 10), date(2026, 2, 10))
        self.assertTrue(created1)
        bs1 = BillingSummary.objects.get(meter=self.meter, period_start=date(2026, 1, 10), period_end=date(2026, 2, 10))
        self.assertEqual(bs1.deemed_method, 'none')
        self.assertTrue(bs1.is_first_billing)
        self.assertEqual(bs1.total_kwh, Decimal('150'))

        # 2回目: 2/10にデータあるが3/10にデータなし
        # → prev_reading(2/10)あり、curr_reading(3/10)なし、期間中なし → みなし
        created2 = process_meter(self.assignment, date(2026, 2, 10), date(2026, 3, 10))
        self.assertTrue(created2)
        bs2 = BillingSummary.objects.get(meter=self.meter, period_start=date(2026, 2, 10), period_end=date(2026, 3, 10))
        self.assertEqual(bs2.deemed_method, 'monthly')

        # 3回目: データなし
        created3 = process_meter(self.assignment, date(2026, 3, 10), date(2026, 4, 10))
        self.assertTrue(created3)
        bs3 = BillingSummary.objects.get(meter=self.meter, period_start=date(2026, 3, 10), period_end=date(2026, 4, 10))
        self.assertEqual(bs3.deemed_method, 'monthly')

        # 4回目: 4/10と5/10にデータあり
        make_30min_readings(self.meter, date(2026, 4, 10), Decimal('700'), Decimal('200'))
        make_30min_readings(self.meter, date(2026, 5, 10), Decimal('900'), Decimal('300'))

        created4 = process_meter(self.assignment, date(2026, 4, 10), date(2026, 5, 10))
        self.assertTrue(created4)
        bs4 = BillingSummary.objects.get(meter=self.meter, period_start=date(2026, 4, 10), period_end=date(2026, 5, 10))
        self.assertEqual(bs4.deemed_method, 'none')
        # prev_used_import=500（bs3から引き継ぎ）, prev_used_export=100
        # 自家消費: (900-500)-(300-100)=400-200=200
        self.assertEqual(bs4.total_kwh, Decimal('200'))

        # みなし調整確認
        first_billing = BillingSummary.objects.get(meter=self.meter, is_first_billing=True)
        actual_cumulative = (
            bs4.curr_used_import - bs4.curr_used_export
        ) - (
            first_billing.curr_used_import - first_billing.curr_used_export
        )
        past_total = BillingSummary.objects.filter(
            meter=self.meter,
            period_end__lte=date(2026, 4, 10),
        ).aggregate(total=Sum('total_kwh'))['total'] or Decimal('0')
        billed_cumulative = past_total + bs4.total_kwh
        adjustment = actual_cumulative - billed_cumulative

        # actual_cumulative = (900-300)-(500-100) = 600-400 = 200
        # first_billingのcurr_used_importは1/10の検針日データ(500)
        self.assertEqual(actual_cumulative, Decimal('200'))
        self.assertLess(adjustment, Decimal('0'))  # みなし分だけマイナスになるはず