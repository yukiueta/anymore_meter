"""
追加テストケース

11. 1回目なし、2回目なし、3回目期中データあり（パターン4）
12. 1回目なし、2回目期中データあり、3回目実測あり（累積引き継ぎ確認）
13. 1回目実測、2回目期中データあり、3回目なし、4回目実測（みなし調整）
14. 期中データ後の次回実測で累積が正しく引き継がれるか
15. メーターリセット（累積値が前回より小さい）→自家消費が0になるケース
"""
from decimal import Decimal
from datetime import date
from django.test import TestCase
from django.db.models import Sum

from app.meters.models import Meter, MeterAssignment
from app.readings.models import MeterReading
from app.billing.models import BillingCalendar, BillingSummary
from app.billing.tasks import calculate_billing, get_deemed_daily_kwh

import datetime
from django.utils import timezone


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


def make_reading(meter, dt, import_kwh, export_kwh):
    ts = timezone.make_aware(datetime.datetime.combine(dt, datetime.time(12, 0)))
    return MeterReading.objects.create(
        meter=meter,
        timestamp=ts,
        reading_type='interval',
        import_kwh=import_kwh,
        export_kwh=Decimal('0'),
        route_b_import_kwh=Decimal('0'),
        route_b_export_kwh=export_kwh,
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


class CalculateBillingExtraTest(TestCase):

    def setUp(self):
        self.meter = make_meter()
        self.assignment = make_assignment(self.meter)

    # =========================================================
    # ケース11: 1回目なし、2回目なし、3回目期中データあり
    # =========================================================
    def test_case11_two_monthly_then_partial(self):
        """
        1回目: データなし → みなし6×31=186, curr_used_import=0, curr_used_export=0
        2回目: データなし → みなし6×28=168, curr_used_import=0, curr_used_export=0
        3回目: 期末なし、期中(3/20)にデータあり 発電200, 売電50
          prev_used_import=0（2回目から引き継ぎ）
          実測分: (200-0)-(50-0)=150kWh
          みなし分: (4/10-3/20)=21日 × 6kWh=126kWh
          合計: 276kWh
        """
        bs1 = make_billing_summary(
            self.meter, date(2026, 1, 10), date(2026, 2, 10),
            Decimal('186'), 'monthly',
            curr_used_import=Decimal('0'), curr_used_export=Decimal('0'),
            is_first_billing=True,
        )
        bs2 = make_billing_summary(
            self.meter, date(2026, 2, 10), date(2026, 3, 10),
            Decimal('168'), 'monthly',
            curr_used_import=Decimal('0'), curr_used_export=Decimal('0'),
        )

        make_reading(self.meter, date(2026, 3, 20), Decimal('200'), Decimal('50'))

        result3 = calculate_billing(
            meter=self.meter,
            prev_billing=bs2,
            prev_import=None,
            prev_export=None,
            curr_import=None,
            curr_export=None,
            period_start=date(2026, 3, 10),
            period_end=date(2026, 4, 10),
            deemed_daily_kwh=Decimal('6.0'),
        )
        self.assertEqual(result3['deemed_method'], 'daily')
        remaining_days = (date(2026, 4, 10) - date(2026, 3, 20)).days  # 21日
        expected_deemed = Decimal('6.0') * remaining_days
        expected_actual = Decimal('150')  # (200-0)-(50-0)
        self.assertEqual(result3['actual_kwh'], expected_actual)
        self.assertEqual(result3['deemed_kwh'], expected_deemed)
        self.assertEqual(result3['total_kwh'], expected_actual + expected_deemed)
        # 期中データで引き継ぎ
        self.assertEqual(result3['curr_used_import'], Decimal('200'))
        self.assertEqual(result3['curr_used_export'], Decimal('50'))

    # =========================================================
    # ケース12: 1回目なし、2回目期中データあり、3回目実測あり
    # =========================================================
    def test_case12_monthly_partial_then_actual(self):
        """
        1回目: データなし → みなし6×31=186, curr_used_import=0, curr_used_export=0
        2回目: 期末なし、期中(2/20)にデータあり 発電300, 売電80
          実測分: (300-0)-(80-0)=220kWh
          みなし分: (3/10-2/20)=19日 × 6kWh=114kWh
          合計: 334kWh
          curr_used_import=300, curr_used_export=80（期中値で引き継ぎ）
        3回目: 発電500, 売電130
          prev_used_import=300, prev_used_export=80（2回目から引き継ぎ）
          自家消費: (500-300)-(130-80)=200-50=150kWh
        """
        bs1 = make_billing_summary(
            self.meter, date(2026, 1, 10), date(2026, 2, 10),
            Decimal('186'), 'monthly',
            curr_used_import=Decimal('0'), curr_used_export=Decimal('0'),
            is_first_billing=True,
        )

        make_reading(self.meter, date(2026, 2, 20), Decimal('300'), Decimal('80'))

        result2 = calculate_billing(
            meter=self.meter,
            prev_billing=bs1,
            prev_import=None,
            prev_export=None,
            curr_import=None,
            curr_export=None,
            period_start=date(2026, 2, 10),
            period_end=date(2026, 3, 10),
            deemed_daily_kwh=Decimal('6.0'),
        )
        self.assertEqual(result2['deemed_method'], 'daily')
        self.assertEqual(result2['actual_kwh'], Decimal('220'))
        remaining_days2 = (date(2026, 3, 10) - date(2026, 2, 20)).days
        self.assertEqual(result2['deemed_kwh'], Decimal('6.0') * remaining_days2)
        self.assertEqual(result2['curr_used_import'], Decimal('300'))
        self.assertEqual(result2['curr_used_export'], Decimal('80'))

        bs2 = make_billing_summary(
            self.meter, date(2026, 2, 10), date(2026, 3, 10),
            result2['total_kwh'], 'daily',
            curr_used_import=Decimal('300'), curr_used_export=Decimal('80'),
        )

        result3 = calculate_billing(
            meter=self.meter,
            prev_billing=bs2,
            prev_import=Decimal('300'),
            prev_export=Decimal('80'),
            curr_import=Decimal('500'),
            curr_export=Decimal('130'),
            period_start=date(2026, 3, 10),
            period_end=date(2026, 4, 10),
        )
        self.assertEqual(result3['deemed_method'], 'none')
        self.assertEqual(result3['total_kwh'], Decimal('150'))
        self.assertEqual(result3['curr_used_import'], Decimal('500'))
        self.assertEqual(result3['curr_used_export'], Decimal('130'))

    # =========================================================
    # ケース13: 実測→期中→なし→実測（みなし調整確認）
    # =========================================================
    def test_case13_actual_partial_monthly_actual_adjustment(self):
        """
        1回目: 発電500, 売電100 → 自家消費400
          curr_used_import=500, curr_used_export=100
        2回目: 期中(2/20)にデータあり 発電600, 売電150
          実測分: (600-500)-(150-100)=50
          みなし: 19日×6=114
          合計: 164
          curr_used_import=600, curr_used_export=150
        3回目: データなし → みなし
          curr_used_import=600, curr_used_export=150（引き継ぎ）
        4回目: 発電900, 売電250
          prev_used_import=600, prev_used_export=150
          自家消費: (900-600)-(250-150)=300-100=200
        調整:
          actual_cumulative=(900-250)-(500-100)=650-400=250
          billed_cumulative=400+164+みなし3+200
        """
        bs1 = make_billing_summary(
            self.meter, date(2026, 1, 10), date(2026, 2, 10),
            Decimal('400'), 'none',
            curr_used_import=Decimal('500'), curr_used_export=Decimal('100'),
            is_first_billing=True,
        )

        make_reading(self.meter, date(2026, 2, 20), Decimal('600'), Decimal('150'))

        result2 = calculate_billing(
            meter=self.meter,
            prev_billing=bs1,
            prev_import=Decimal('500'),
            prev_export=Decimal('100'),
            curr_import=None,
            curr_export=None,
            period_start=date(2026, 2, 10),
            period_end=date(2026, 3, 10),
            deemed_daily_kwh=Decimal('6.0'),
        )
        self.assertEqual(result2['deemed_method'], 'daily')
        self.assertEqual(result2['actual_kwh'], Decimal('50'))
        self.assertEqual(result2['curr_used_import'], Decimal('600'))
        self.assertEqual(result2['curr_used_export'], Decimal('150'))

        bs2 = make_billing_summary(
            self.meter, date(2026, 2, 10), date(2026, 3, 10),
            result2['total_kwh'], 'daily',
            curr_used_import=Decimal('600'), curr_used_export=Decimal('150'),
        )

        # 3回目（みなし）
        deemed_daily3 = get_deemed_daily_kwh(self.meter, date(2026, 4, 10))
        result3 = calculate_billing(
            meter=self.meter,
            prev_billing=bs2,
            prev_import=None,
            prev_export=None,
            curr_import=None,
            curr_export=None,
            period_start=date(2026, 3, 10),
            period_end=date(2026, 4, 10),
            deemed_daily_kwh=deemed_daily3,
        )
        self.assertEqual(result3['deemed_method'], 'monthly')
        # みなし時はcurr_used_import/exportは引き継ぎ
        self.assertEqual(result3['curr_used_import'], Decimal('600'))
        self.assertEqual(result3['curr_used_export'], Decimal('150'))

        bs3 = make_billing_summary(
            self.meter, date(2026, 3, 10), date(2026, 4, 10),
            result3['total_kwh'], 'monthly',
            curr_used_import=Decimal('600'), curr_used_export=Decimal('150'),
        )

        # 4回目（実測）
        result4 = calculate_billing(
            meter=self.meter,
            prev_billing=bs3,
            prev_import=Decimal('600'),
            prev_export=Decimal('150'),
            curr_import=Decimal('900'),
            curr_export=Decimal('250'),
            period_start=date(2026, 4, 10),
            period_end=date(2026, 5, 10),
        )
        self.assertEqual(result4['deemed_method'], 'none')
        self.assertEqual(result4['total_kwh'], Decimal('200'))

        # みなし調整
        past_total = BillingSummary.objects.filter(
            meter=self.meter,
            period_end__lte=date(2026, 4, 10),
        ).aggregate(total=Sum('total_kwh'))['total'] or Decimal('0')

        first_billing = BillingSummary.objects.get(meter=self.meter, is_first_billing=True)
        actual_cumulative = (
            result4['curr_used_import'] - result4['curr_used_export']
        ) - (
            first_billing.curr_used_import - first_billing.curr_used_export
        )
        billed_cumulative = past_total + result4['total_kwh']
        adjustment = actual_cumulative - billed_cumulative

        # actual_cumulative = (900-250)-(500-100) = 650-400 = 250
        self.assertEqual(actual_cumulative, Decimal('250'))
        # billed_cumulative = 400 + 164 + みなし3 + 200
        expected_billed = Decimal('400') + result2['total_kwh'] + result3['total_kwh'] + Decimal('200')
        self.assertEqual(billed_cumulative, expected_billed)
        self.assertEqual(adjustment, Decimal('250') - expected_billed)

    # =========================================================
    # ケース14: 期中データ後の次回実測で累積が正しく引き継がれるか
    # =========================================================
    def test_case14_partial_continuity(self):
        """
        期中データで引き継いだcurr_used_import/exportが
        次回の計算で正しくprev_used_import/exportとして使われるか確認

        1回目: 発電200, 売電50 → 自家消費150
        2回目: 期中(2/20)にデータあり 発電350, 売電90
          実測: (350-200)-(90-50)=150-40=110
          みなし: 19日×6=114
          curr_used_import=350, curr_used_export=90
        3回目: 発電500, 売電130
          prev_used_import=350（2回目期中値）, prev_used_export=90
          自家消費: (500-350)-(130-90)=150-40=110
        4回目: 発電700, 売電200
          prev_used_import=500, prev_used_export=130
          自家消費: (700-500)-(200-130)=200-70=130
        """
        bs1 = make_billing_summary(
            self.meter, date(2026, 1, 10), date(2026, 2, 10),
            Decimal('150'), 'none',
            curr_used_import=Decimal('200'), curr_used_export=Decimal('50'),
            is_first_billing=True,
        )

        make_reading(self.meter, date(2026, 2, 20), Decimal('350'), Decimal('90'))

        result2 = calculate_billing(
            meter=self.meter,
            prev_billing=bs1,
            prev_import=Decimal('200'),
            prev_export=Decimal('50'),
            curr_import=None,
            curr_export=None,
            period_start=date(2026, 2, 10),
            period_end=date(2026, 3, 10),
            deemed_daily_kwh=Decimal('6.0'),
        )
        self.assertEqual(result2['actual_kwh'], Decimal('110'))
        self.assertEqual(result2['curr_used_import'], Decimal('350'))
        self.assertEqual(result2['curr_used_export'], Decimal('90'))

        bs2 = make_billing_summary(
            self.meter, date(2026, 2, 10), date(2026, 3, 10),
            result2['total_kwh'], 'daily',
            curr_used_import=Decimal('350'), curr_used_export=Decimal('90'),
        )

        result3 = calculate_billing(
            meter=self.meter,
            prev_billing=bs2,
            prev_import=Decimal('350'),
            prev_export=Decimal('90'),
            curr_import=Decimal('500'),
            curr_export=Decimal('130'),
            period_start=date(2026, 3, 10),
            period_end=date(2026, 4, 10),
        )
        self.assertEqual(result3['deemed_method'], 'none')
        self.assertEqual(result3['total_kwh'], Decimal('110'))

        bs3 = make_billing_summary(
            self.meter, date(2026, 3, 10), date(2026, 4, 10),
            Decimal('110'), 'none',
            curr_used_import=Decimal('500'), curr_used_export=Decimal('130'),
        )

        result4 = calculate_billing(
            meter=self.meter,
            prev_billing=bs3,
            prev_import=Decimal('500'),
            prev_export=Decimal('130'),
            curr_import=Decimal('700'),
            curr_export=Decimal('200'),
            period_start=date(2026, 4, 10),
            period_end=date(2026, 5, 10),
        )
        self.assertEqual(result4['deemed_method'], 'none')
        self.assertEqual(result4['total_kwh'], Decimal('130'))

    # =========================================================
    # ケース15: メーターリセット（累積値が前回より小さい）
    # =========================================================
    def test_case15_meter_reset(self):
        """
        メーターリセットにより累積値が前回より小さくなるケース
        自家消費がマイナスになるのでmax(0)で0になる

        1回目: 発電500, 売電100 → 自家消費400
        2回目: 発電50, 売電10（リセット後）
          prev_used_import=500, curr_import=50
          generation_delta = 50-500 = -450 → 自家消費=max(0, -450-(-90))=0
        """
        bs1 = make_billing_summary(
            self.meter, date(2026, 1, 10), date(2026, 2, 10),
            Decimal('400'), 'none',
            curr_used_import=Decimal('500'), curr_used_export=Decimal('100'),
            is_first_billing=True,
        )

        result2 = calculate_billing(
            meter=self.meter,
            prev_billing=bs1,
            prev_import=Decimal('500'),
            prev_export=Decimal('100'),
            curr_import=Decimal('50'),
            curr_export=Decimal('10'),
            period_start=date(2026, 2, 10),
            period_end=date(2026, 3, 10),
        )
        self.assertEqual(result2['deemed_method'], 'none')
        self.assertEqual(result2['total_kwh'], Decimal('0'))  # max(0, マイナス)