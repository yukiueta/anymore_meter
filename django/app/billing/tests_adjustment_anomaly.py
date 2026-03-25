"""
みなし調整（5パターン）と異常値（5パターン）のテスト

みなし調整:
A1. 1回みなし後の実測（調整小）
A2. 連続3回みなし後の実測（調整大）
A3. みなし後の実測（調整は常にみなし分のマイナス）
A4. 期中データ含むみなし後の実測（調整確認）
A5. 初回みなし→実測→みなし→実測（複雑な引き継ぎ）

異常値:
B1. 前月比20倍超（異常値アラート発生）
B2. 前月比1/20以下（異常値アラート発生）
B3. 売電量が発電量を上回る（自家消費0）
B4. メーターリセット（累積値が前回より小さい→自家消費0）
B5. 同一検針日に複数レコード（最新が使われるか）
"""
from decimal import Decimal
from datetime import date
import datetime
from django.test import TestCase
from django.utils import timezone
from django.db.models import Sum
from unittest.mock import patch

from app.meters.models import Meter, MeterAssignment
from app.readings.models import MeterReading
from app.billing.models import BillingCalendar, BillingSummary
from app.alerts.models import Alert
from app.billing.tasks import process_meter


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


def make_reading(meter, dt, import_kwh, export_kwh, time=datetime.time(12, 0)):
    ts = timezone.make_aware(datetime.datetime.combine(dt, time))
    return MeterReading.objects.create(
        meter=meter,
        timestamp=ts,
        reading_type='interval',
        import_kwh=Decimal(str(import_kwh)),
        export_kwh=Decimal('0'),
        route_b_import_kwh=Decimal('0'),
        route_b_export_kwh=Decimal(str(export_kwh)),
    )


def make_billing_summary(meter, period_start, period_end, total_kwh, deemed_method='none',
                          curr_used_import=None, curr_used_export=None,
                          is_first_billing=False):
    return BillingSummary.objects.create(
        meter=meter,
        project_id=1,
        project_name='テスト案件',
        zone=3,
        base_billing_day='10',
        period_start=period_start,
        period_end=period_end,
        prev_used_import=Decimal('0'),
        curr_used_import=curr_used_import if curr_used_import is not None else Decimal(str(total_kwh)),
        prev_used_export=Decimal('0'),
        curr_used_export=curr_used_export if curr_used_export is not None else Decimal('0'),
        actual_kwh=total_kwh if deemed_method == 'none' else Decimal('0'),
        deemed_kwh=total_kwh if deemed_method != 'none' else Decimal('0'),
        total_kwh=total_kwh,
        deemed_method=deemed_method,
        is_first_billing=is_first_billing,
    )


class DeemedAdjustmentTest(TestCase):

    def setUp(self):
        self.meter = make_meter()
        self.assignment = make_assignment(self.meter)

    def _calc_adjustment(self, bs, period_end):
        past_total = BillingSummary.objects.filter(
            meter=self.meter,
            period_end__lte=period_end,
        ).aggregate(total=Sum('total_kwh'))['total'] or Decimal('0')
        first_billing = BillingSummary.objects.get(meter=self.meter, is_first_billing=True)
        actual_cumulative = (
            bs.curr_used_import - bs.curr_used_export
        ) - (
            first_billing.prev_used_import - first_billing.prev_used_export
        )
        billed_cumulative = past_total + bs.total_kwh
        return actual_cumulative - billed_cumulative

    # =========================================================
    # A1: 1回みなし後の実測（調整小）
    # =========================================================
    
    def test_A1_one_deemed_then_actual(self):
        """
        1回目: 発電300→500(200増), 売電50→100(50増) → 自家消費150
        2回目: データなし → みなし
        3回目: 発電700, 売電200
          prev_used_import=500, prev_used_export=100
          自家消費: (700-500)-(200-100)=100
          actual_cumulative=(700-200)-(300-50)=500-250=250
          billed=150+みなし+100
          adjustment=250-billed → マイナス（みなし分）
        """
        make_reading(self.meter, date(2026, 1, 10), 300, 50)
        make_reading(self.meter, date(2026, 2, 10), 500, 100)

        process_meter(self.assignment, date(2026, 1, 10), date(2026, 2, 10))
        bs1 = BillingSummary.objects.get(meter=self.meter, period_start=date(2026, 1, 10))
        self.assertEqual(bs1.deemed_method, 'none')
        self.assertEqual(bs1.total_kwh, Decimal('150'))

        process_meter(self.assignment, date(2026, 2, 10), date(2026, 3, 10))
        bs2 = BillingSummary.objects.get(meter=self.meter, period_start=date(2026, 2, 10))
        self.assertEqual(bs2.deemed_method, 'monthly')

        make_reading(self.meter, date(2026, 4, 10), 700, 200)
        process_meter(self.assignment, date(2026, 3, 10), date(2026, 4, 10))
        bs3 = BillingSummary.objects.get(meter=self.meter, period_start=date(2026, 3, 10))
        self.assertEqual(bs3.deemed_method, 'none')
        self.assertEqual(bs3.total_kwh, Decimal('100'))

        adjustment = self._calc_adjustment(bs3, date(2026, 3, 10))
        self.assertLess(adjustment, Decimal('0'))
        # みなし1回分だけマイナス
        # adjustment = actual_cumulative - billed_cumulative
        # actual_cumulative = (700-200)-(300-50) = 500-250 = 250
        # billed_cumulative = 150 + bs2.total_kwh + 100
        expected_adjustment = Decimal('250') - (Decimal('150') + bs2.total_kwh + Decimal('100'))
        self.assertEqual(adjustment, expected_adjustment)

    # =========================================================
    # A2: 連続3回みなし後の実測（調整大）
    # =========================================================
    
    def test_A2_three_deemed_then_actual_large_adjustment(self):
        """
        1回目: 発電300→500, 売電50→100 → 自家消費150
        2〜4回目: みなし
        5回目: 発電700, 売電200 → 自家消費100
          adjustment = -（みなし3回分の合計）
        """
        make_reading(self.meter, date(2026, 1, 10), 300, 50)
        make_reading(self.meter, date(2026, 2, 10), 500, 100)

        process_meter(self.assignment, date(2026, 1, 10), date(2026, 2, 10))

        for start, end in [
            (date(2026, 2, 10), date(2026, 3, 10)),
            (date(2026, 3, 10), date(2026, 4, 10)),
            (date(2026, 4, 10), date(2026, 5, 10)),
        ]:
            process_meter(self.assignment, start, end)
            bs = BillingSummary.objects.get(meter=self.meter, period_start=start)
            self.assertEqual(bs.deemed_method, 'monthly')

        make_reading(self.meter, date(2026, 6, 10), 700, 200)
        process_meter(self.assignment, date(2026, 5, 10), date(2026, 6, 10))
        bs5 = BillingSummary.objects.get(meter=self.meter, period_start=date(2026, 5, 10))
        self.assertEqual(bs5.deemed_method, 'none')
        self.assertEqual(bs5.total_kwh, Decimal('100'))

        adjustment = self._calc_adjustment(bs5, date(2026, 5, 10))
        deemed_total = BillingSummary.objects.filter(
            meter=self.meter, deemed_method='monthly'
        ).aggregate(total=Sum('total_kwh'))['total']
        self.assertEqual(adjustment, -deemed_total)

    # =========================================================
    # A3: みなし後の実測（調整は常にみなし分のマイナス）
    # =========================================================
    
    def test_A3_adjustment_equals_negative_deemed(self):
        """
        みなし調整 = -（みなし合計）であることを確認
        実測値の大小に関わらず、みなし分だけマイナスになる
        """
        make_reading(self.meter, date(2026, 1, 10), 100, 10)
        make_reading(self.meter, date(2026, 2, 10), 200, 20)

        process_meter(self.assignment, date(2026, 1, 10), date(2026, 2, 10))
        bs1 = BillingSummary.objects.get(meter=self.meter, period_start=date(2026, 1, 10))
        self.assertEqual(bs1.total_kwh, Decimal('90'))

        # みなし2回
        process_meter(self.assignment, date(2026, 2, 10), date(2026, 3, 10))
        process_meter(self.assignment, date(2026, 3, 10), date(2026, 4, 10))

        deemed_total = BillingSummary.objects.filter(
            meter=self.meter, deemed_method='monthly'
        ).aggregate(total=Sum('total_kwh'))['total']

        # 大きな実測値で実測
        make_reading(self.meter, date(2026, 5, 10), 5000, 1000)
        process_meter(self.assignment, date(2026, 4, 10), date(2026, 5, 10))
        bs4 = BillingSummary.objects.get(meter=self.meter, period_start=date(2026, 4, 10))
        self.assertEqual(bs4.deemed_method, 'none')

        adjustment = self._calc_adjustment(bs4, date(2026, 4, 10))
        self.assertEqual(adjustment, -deemed_total)

    # =========================================================
    # A4: 期中データ含むみなし後の実測
    # =========================================================
    
    def test_A4_partial_deemed_then_actual_adjustment(self):
        """
        1回目: 変化なし → 自家消費0
        2回目: 期中(2/20)データ → daily みなし
        3回目: 実測
          adjustment = -(みなし分のみ)
        """
        make_reading(self.meter, date(2026, 1, 10), 300, 50)
        make_reading(self.meter, date(2026, 2, 10), 300, 50)
        make_reading(self.meter, date(2026, 2, 20), 400, 80)

        process_meter(self.assignment, date(2026, 1, 10), date(2026, 2, 10))
        bs1 = BillingSummary.objects.get(meter=self.meter, period_start=date(2026, 1, 10))
        self.assertEqual(bs1.total_kwh, Decimal('0'))

        process_meter(self.assignment, date(2026, 2, 10), date(2026, 3, 10))
        bs2 = BillingSummary.objects.get(meter=self.meter, period_start=date(2026, 2, 10))
        self.assertEqual(bs2.deemed_method, 'daily')

        make_reading(self.meter, date(2026, 4, 10), 600, 130)
        process_meter(self.assignment, date(2026, 3, 10), date(2026, 4, 10))
        bs3 = BillingSummary.objects.get(meter=self.meter, period_start=date(2026, 3, 10))
        self.assertEqual(bs3.deemed_method, 'none')

        adjustment = self._calc_adjustment(bs3, date(2026, 3, 10))
        # みなし分(bs2.deemed_kwh)だけマイナス
        self.assertEqual(adjustment, -bs2.deemed_kwh)

    # =========================================================
    # A5: 初回みなし→実測→みなし→実測
    # =========================================================
    
    def test_A5_deemed_actual_deemed_actual(self):
        """
        みなし→実測→みなし→実測のサイクル
        各実測時のadjustmentが直前のみなし分のマイナスになるか確認
        """
        # 1回目: みなし
        process_meter(self.assignment, date(2026, 1, 10), date(2026, 2, 10))
        bs1 = BillingSummary.objects.get(meter=self.meter, period_start=date(2026, 1, 10))
        self.assertEqual(bs1.deemed_method, 'monthly')

        # 2回目: 実測
        make_reading(self.meter, date(2026, 2, 10), 500, 100)
        make_reading(self.meter, date(2026, 3, 10), 500, 100)
        process_meter(self.assignment, date(2026, 2, 10), date(2026, 3, 10))
        bs2 = BillingSummary.objects.get(meter=self.meter, period_start=date(2026, 2, 10))
        self.assertEqual(bs2.deemed_method, 'none')

        adjustment2 = self._calc_adjustment(bs2, date(2026, 2, 10))
        # 最初のみなし分だけマイナス
        self.assertEqual(adjustment2, -bs1.total_kwh)

        # 3回目: みなし
        process_meter(self.assignment, date(2026, 3, 10), date(2026, 4, 10))
        bs3 = BillingSummary.objects.get(meter=self.meter, period_start=date(2026, 3, 10))
        self.assertEqual(bs3.deemed_method, 'monthly')

        # 4回目: 実測
        make_reading(self.meter, date(2026, 5, 10), 700, 200)
        process_meter(self.assignment, date(2026, 4, 10), date(2026, 5, 10))
        bs4 = BillingSummary.objects.get(meter=self.meter, period_start=date(2026, 4, 10))
        self.assertEqual(bs4.deemed_method, 'none')

        adjustment4 = self._calc_adjustment(bs4, date(2026, 4, 10))
        # みなし2回分（bs1+bs3）だけマイナス
        self.assertEqual(adjustment4, -(bs1.total_kwh + bs3.total_kwh))


class AnomalyTest(TestCase):

    def setUp(self):
        self.meter = make_meter()
        self.assignment = make_assignment(self.meter)

    # =========================================================
    # B1: 前月比20倍超（異常値アラート発生）
    # =========================================================
    def test_B1_twenty_times_anomaly(self):
        """
        前月: 10kWh
        今月: 210kWh（21倍）→ アラート発生
        """
        make_billing_summary(
            self.meter, date(2026, 1, 10), date(2026, 2, 10),
            Decimal('10'), 'none',
            curr_used_import=Decimal('100'), curr_used_export=Decimal('90'),
            is_first_billing=True,
        )

        make_reading(self.meter, date(2026, 2, 10), 100, 90)
        make_reading(self.meter, date(2026, 3, 10), 310, 90)

        process_meter(self.assignment, date(2026, 2, 10), date(2026, 3, 10))
        bs = BillingSummary.objects.get(meter=self.meter, period_start=date(2026, 2, 10))
        self.assertEqual(bs.total_kwh, Decimal('210'))

        alert = Alert.objects.filter(meter=self.meter, alert_type='anomaly').first()
        self.assertIsNotNone(alert)
        self.assertIn('20倍', alert.message)

    # =========================================================
    # B2: 前月比1/20以下（異常値アラート発生）
    # =========================================================
    def test_B2_one_twentieth_anomaly(self):
        """
        前月: 200kWh
        今月: 5kWh（1/40）→ アラート発生
        """
        make_billing_summary(
            self.meter, date(2026, 1, 10), date(2026, 2, 10),
            Decimal('200'), 'none',
            curr_used_import=Decimal('500'), curr_used_export=Decimal('300'),
            is_first_billing=True,
        )

        make_reading(self.meter, date(2026, 2, 10), 500, 300)
        make_reading(self.meter, date(2026, 3, 10), 505, 300)

        process_meter(self.assignment, date(2026, 2, 10), date(2026, 3, 10))
        bs = BillingSummary.objects.get(meter=self.meter, period_start=date(2026, 2, 10))
        self.assertEqual(bs.total_kwh, Decimal('5'))

        alert = Alert.objects.filter(meter=self.meter, alert_type='anomaly').first()
        self.assertIsNotNone(alert)
        self.assertIn('1/20', alert.message)

    # =========================================================
    # B3: 売電量が発電量を上回る（自家消費0）
    # =========================================================
    
    def test_B3_export_exceeds_import(self):
        """
        発電増分100, 売電増分150 → 自家消費=max(0,-50)=0
        """
        make_reading(self.meter, date(2026, 1, 10), 500, 100)
        make_reading(self.meter, date(2026, 2, 10), 600, 250)

        process_meter(self.assignment, date(2026, 1, 10), date(2026, 2, 10))
        bs = BillingSummary.objects.get(meter=self.meter, period_start=date(2026, 1, 10))
        self.assertEqual(bs.deemed_method, 'none')
        self.assertEqual(bs.total_kwh, Decimal('0'))
        self.assertEqual(bs.actual_kwh, Decimal('0'))

    # =========================================================
    # B4: メーターリセット（累積値が前回より小さい）
    # =========================================================
    
    def test_B4_meter_reset(self):
        """
        1回目: 自家消費400
        2回目: リセット後 発電50, 売電10 → 自家消費=max(0,...)=0
        """
        make_reading(self.meter, date(2026, 1, 10), 500, 100)
        make_reading(self.meter, date(2026, 2, 10), 1000, 200)

        process_meter(self.assignment, date(2026, 1, 10), date(2026, 2, 10))
        bs1 = BillingSummary.objects.get(meter=self.meter, period_start=date(2026, 1, 10))
        self.assertEqual(bs1.total_kwh, Decimal('400'))

        make_reading(self.meter, date(2026, 3, 10), 50, 10)

        process_meter(self.assignment, date(2026, 2, 10), date(2026, 3, 10))
        bs2 = BillingSummary.objects.get(meter=self.meter, period_start=date(2026, 2, 10))
        self.assertEqual(bs2.deemed_method, 'none')
        self.assertEqual(bs2.total_kwh, Decimal('0'))

    # =========================================================
    # B5: 同一検針日に複数レコード（最新が使われるか）
    # =========================================================
    
    def test_B5_multiple_records_same_date(self):
        """
        2/10に12:00(600/150)と23:30(700/200)の2レコード
        最新の23:30(700/200)が使われる
        prev=300/50, curr=700/200
        自家消費=(700-300)-(200-50)=400-150=250
        """
        make_reading(self.meter, date(2026, 1, 10), 300, 50, datetime.time(12, 0))
        make_reading(self.meter, date(2026, 2, 10), 600, 150, datetime.time(12, 0))
        make_reading(self.meter, date(2026, 2, 10), 700, 200, datetime.time(23, 30))

        process_meter(self.assignment, date(2026, 1, 10), date(2026, 2, 10))
        bs = BillingSummary.objects.get(meter=self.meter, period_start=date(2026, 1, 10))
        self.assertEqual(bs.deemed_method, 'none')
        self.assertEqual(bs.total_kwh, Decimal('250'))
        self.assertEqual(bs.curr_used_import, Decimal('700'))
        self.assertEqual(bs.curr_used_export, Decimal('200'))