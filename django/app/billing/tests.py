"""
calculate_billing / process_meter のユニットテスト

テストケース:
1. 全期間実測（正常ケース）
2. 初回のみ実測、以降2回みなし後に実測（みなし調整あり）
3. 初回なし、2回目から実測
4. 中間1回みなし（期間中データあり、パターン4）
5. 連続2回みなし後に実測
6. 連続3回みなし後に実測（みなし調整が大きいケース）
7. 初回からデータなし→実測
8. みなし後に実測値がみなし累計を大きく下回るケース（調整がマイナス大）
9. 売電量が大きく自家消費がゼロになるケース
10. みなし日次単価が6kWh/日を上回るケース（直近12ヶ月平均が高い）
"""
from decimal import Decimal
from datetime import date, timedelta
from django.test import TestCase

from app.meters.models import Meter, MeterAssignment
from app.readings.models import MeterReading
from app.billing.models import BillingCalendar, BillingSummary
from app.billing.tasks import calculate_billing, get_deemed_daily_kwh, process_meter


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
    from django.utils import timezone
    import datetime
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


class CalculateBillingTest(TestCase):

    def setUp(self):
        self.meter = make_meter()
        self.assignment = make_assignment(self.meter)

    # =========================================================
    # ケース1: 全期間実測（正常ケース）
    # =========================================================
    def test_case1_all_actual(self):
        """
        1回目: 発電500, 売電100 → 自家消費400
        2回目: 発電700, 売電200 → 自家消費200（増分200-100）
        3回目: 発電1000, 売電350 → 自家消費300（増分300-150）
        """
        # 1回目
        result = calculate_billing(
            meter=self.meter,
            prev_billing=None,
            prev_import=None,
            prev_export=None,
            curr_import=Decimal('500'),
            curr_export=Decimal('100'),
            period_start=date(2026, 1, 10),
            period_end=date(2026, 2, 10),
        )
        self.assertEqual(result['total_kwh'], Decimal('400'))
        self.assertEqual(result['deemed_method'], 'none')
        self.assertTrue(result['is_first_billing'])
        self.assertEqual(result['curr_used_import'], Decimal('500'))
        self.assertEqual(result['curr_used_export'], Decimal('100'))

        # 1回目を保存
        bs1 = make_billing_summary(
            self.meter, date(2026, 1, 10), date(2026, 2, 10),
            Decimal('400'), 'none',
            curr_used_import=Decimal('500'), curr_used_export=Decimal('100'),
            is_first_billing=True,
        )

        # 2回目
        result2 = calculate_billing(
            meter=self.meter,
            prev_billing=bs1,
            prev_import=Decimal('500'),
            prev_export=Decimal('100'),
            curr_import=Decimal('700'),
            curr_export=Decimal('200'),
            period_start=date(2026, 2, 10),
            period_end=date(2026, 3, 10),
        )
        self.assertEqual(result2['total_kwh'], Decimal('100'))
        self.assertEqual(result2['deemed_method'], 'none')
        self.assertEqual(result2['curr_used_import'], Decimal('700'))
        self.assertEqual(result2['curr_used_export'], Decimal('200'))

    # =========================================================
    # ケース2: 初回実測 → 2回みなし → 実測（みなし調整あり）
    # =========================================================
    def test_case2_deemed_then_actual_with_adjustment(self):
        """
        1回目: 発電500, 売電100 → 自家消費400
        2回目: データなし → みなし（daily_avg=400/31≒12.9 → 12.9×31≒400）
        3回目: データなし → みなし
        4回目: 発電700, 売電200 → 自家消費100
          調整: actual_cumulative=(700-200)-(500-100)=100, billed=400+400+400+100=1300 → 調整=-1200
        """

        # 1回目保存
        bs1 = make_billing_summary(
            self.meter, date(2026, 1, 10), date(2026, 2, 10),
            Decimal('400'), 'none',
            curr_used_import=Decimal('500'), curr_used_export=Decimal('100'),
            is_first_billing=True,
        )

        # 2回目（みなし）
        deemed_daily = get_deemed_daily_kwh(self.meter, date(2026, 3, 10))
        result2 = calculate_billing(
            meter=self.meter,
            prev_billing=bs1,
            prev_import=None,
            prev_export=None,
            curr_import=None,
            curr_export=None,
            period_start=date(2026, 2, 10),
            period_end=date(2026, 3, 10),
            deemed_daily_kwh=deemed_daily,
        )
        self.assertEqual(result2['deemed_method'], 'monthly')
        days2 = (date(2026, 3, 10) - date(2026, 2, 10)).days
        expected_deemed2 = deemed_daily * days2
        self.assertEqual(result2['total_kwh'], expected_deemed2)

        bs2 = make_billing_summary(
            self.meter, date(2026, 2, 10), date(2026, 3, 10),
            expected_deemed2, 'monthly',
            curr_used_import=Decimal('500'), curr_used_export=Decimal('100'),
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

        bs3 = make_billing_summary(
            self.meter, date(2026, 3, 10), date(2026, 4, 10),
            result3['total_kwh'], 'monthly',
            curr_used_import=Decimal('500'), curr_used_export=Decimal('100'),
        )

        # 4回目（実測）
        result4 = calculate_billing(
            meter=self.meter,
            prev_billing=bs3,
            prev_import=None,
            prev_export=None,
            curr_import=Decimal('700'),
            curr_export=Decimal('200'),
            period_start=date(2026, 4, 10),
            period_end=date(2026, 5, 10),
        )
        self.assertEqual(result4['total_kwh'], Decimal('100'))
        self.assertEqual(result4['deemed_method'], 'none')

        # みなし調整計算
        from django.db.models import Sum
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
        deemed_adjustment = actual_cumulative - billed_cumulative

        self.assertLess(deemed_adjustment, Decimal('0'))  # マイナス調整

    # =========================================================
    # ケース3: 初回データなし → 2回目から実測
    # =========================================================
    def test_case3_no_first_data(self):
        """
        1回目: データなし → みなし
        2回目: 発電500, 売電100 → 自家消費計算
        """
        days = 31
        deemed_daily = Decimal('6.0')

        result1 = calculate_billing(
            meter=self.meter,
            prev_billing=None,
            prev_import=None,
            prev_export=None,
            curr_import=None,
            curr_export=None,
            period_start=date(2026, 1, 10),
            period_end=date(2026, 2, 10),
            deemed_daily_kwh=deemed_daily,
        )
        self.assertEqual(result1['deemed_method'], 'monthly')
        self.assertTrue(result1['is_first_billing'])
        self.assertEqual(result1['total_kwh'], deemed_daily * days)

        bs1 = make_billing_summary(
            self.meter, date(2026, 1, 10), date(2026, 2, 10),
            deemed_daily * days, 'monthly',
            curr_used_import=Decimal('0'), curr_used_export=Decimal('0'),
            is_first_billing=True,
        )

        result2 = calculate_billing(
            meter=self.meter,
            prev_billing=bs1,
            prev_import=Decimal('500'),
            prev_export=Decimal('100'),
            curr_import=Decimal('500'),
            curr_export=Decimal('100'),
            period_start=date(2026, 2, 10),
            period_end=date(2026, 3, 10),
        )
        # prev_used_import=0（bs1のcurr_used_import）なので全累積が自家消費になる
        self.assertEqual(result2['total_kwh'], Decimal('400'))
        self.assertEqual(result2['deemed_method'], 'none')

    # =========================================================
    # ケース4: 期間中データあり（パターン4）
    # =========================================================
    def test_case4_mid_period_data(self):
        """
        1回目: 発電500, 売電100 → 自家消費400
        2回目: 期末データなし、期中(2/20)にデータあり 発電600, 売電150
          実測分: (600-500)-(150-100)=50kWh
          みなし分: (3/10-2/20)=18日 × 6kWh = 108kWh
          合計: 158kWh
        """
        bs1 = make_billing_summary(
            self.meter, date(2026, 1, 10), date(2026, 2, 10),
            Decimal('400'), 'none',
            curr_used_import=Decimal('500'), curr_used_export=Decimal('100'),
            is_first_billing=True,
        )

        # 期中データを作成
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
        remaining_days = (date(2026, 3, 10) - date(2026, 2, 20)).days  # 19日
        expected_deemed = Decimal('6.0') * remaining_days
        expected_actual = Decimal('50')
        self.assertEqual(result2['actual_kwh'], expected_actual)
        self.assertEqual(result2['deemed_kwh'], expected_deemed)
        self.assertEqual(result2['total_kwh'], expected_actual + expected_deemed)

    # =========================================================
    # ケース5: 連続2回みなし後に実測
    # =========================================================
    def test_case5_two_deemed_then_actual(self):
        """
        1回目: 発電300, 売電50 → 自家消費250
        2回目: データなし → みなし6×31=186
        3回目: データなし → みなし6×28=168
        4回目: 発電600, 売電100 → 自家消費(600-300)-(100-50)=250
        """
        bs1 = make_billing_summary(
            self.meter, date(2026, 1, 10), date(2026, 2, 10),
            Decimal('250'), 'none',
            curr_used_import=Decimal('300'), curr_used_export=Decimal('50'),
            is_first_billing=True,
        )

        bs2 = make_billing_summary(
            self.meter, date(2026, 2, 10), date(2026, 3, 10),
            Decimal('186'), 'monthly',
            curr_used_import=Decimal('300'), curr_used_export=Decimal('50'),
        )

        bs3 = make_billing_summary(
            self.meter, date(2026, 3, 10), date(2026, 4, 10),
            Decimal('168'), 'monthly',
            curr_used_import=Decimal('300'), curr_used_export=Decimal('50'),
        )

        result4 = calculate_billing(
            meter=self.meter,
            prev_billing=bs3,
            prev_import=None,
            prev_export=None,
            curr_import=Decimal('600'),
            curr_export=Decimal('100'),
            period_start=date(2026, 4, 10),
            period_end=date(2026, 5, 10),
        )
        self.assertEqual(result4['total_kwh'], Decimal('250'))
        self.assertEqual(result4['deemed_method'], 'none')
        self.assertEqual(result4['curr_used_import'], Decimal('600'))
        self.assertEqual(result4['curr_used_export'], Decimal('100'))

    # =========================================================
    # ケース6: 連続3回みなし後に実測（調整大）
    # =========================================================
    def test_case6_three_deemed_large_adjustment(self):
        """
        1回目: 発電1000, 売電800 → 自家消費200
        2〜4回目: みなし6×30=180ずつ
        5回目: 発電1100, 売電870 → 自家消費(100-70)=30
        調整: actual_cumulative=(1100-870)-(1000-800)=230-200=30
              billed=200+180+180+180+30=770
              adjustment=30-770=-740
        """
        bs1 = make_billing_summary(
            self.meter, date(2026, 1, 10), date(2026, 2, 10),
            Decimal('200'), 'none',
            curr_used_import=Decimal('1000'), curr_used_export=Decimal('800'),
            is_first_billing=True,
        )
        prev = bs1
        for i, (start, end) in enumerate([
            (date(2026, 2, 10), date(2026, 3, 10)),
            (date(2026, 3, 10), date(2026, 4, 10)),
            (date(2026, 4, 10), date(2026, 5, 10)),
        ]):
            prev = make_billing_summary(
                self.meter, start, end,
                Decimal('180'), 'monthly',
                curr_used_import=Decimal('1000'), curr_used_export=Decimal('800'),
            )

        result5 = calculate_billing(
            meter=self.meter,
            prev_billing=prev,
            prev_import=None,
            prev_export=None,
            curr_import=Decimal('1100'),
            curr_export=Decimal('870'),
            period_start=date(2026, 5, 10),
            period_end=date(2026, 6, 10),
        )
        self.assertEqual(result5['total_kwh'], Decimal('30'))

        from django.db.models import Sum
        past_total = BillingSummary.objects.filter(
            meter=self.meter,
            period_end__lte=date(2026, 5, 10),
        ).aggregate(total=Sum('total_kwh'))['total'] or Decimal('0')

        first_billing = BillingSummary.objects.get(meter=self.meter, is_first_billing=True)
        actual_cumulative = (
            result5['curr_used_import'] - result5['curr_used_export']
        ) - (
            first_billing.curr_used_import - first_billing.curr_used_export
        )
        billed_cumulative = past_total + result5['total_kwh']
        adjustment = actual_cumulative - billed_cumulative

        self.assertEqual(adjustment, Decimal('-740'))

    # =========================================================
    # ケース7: 初回からデータなし → 実測
    # =========================================================
    def test_case7_no_data_then_actual(self):
        """
        1〜2回目: データなし → みなし
        3回目: 発電200, 売電50 → 自家消費150
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

        result3 = calculate_billing(
            meter=self.meter,
            prev_billing=bs2,
            prev_import=Decimal('200'),
            prev_export=Decimal('50'),
            curr_import=Decimal('200'),
            curr_export=Decimal('50'),
            period_start=date(2026, 3, 10),
            period_end=date(2026, 4, 10),
        )
        # prev_used_import=0なので累積全体が対象
        self.assertEqual(result3['total_kwh'], Decimal('150'))
        self.assertEqual(result3['deemed_method'], 'none')

    # =========================================================
    # ケース8: みなし後に実測値がみなし累計を大きく下回る
    # =========================================================
    def test_case8_actual_far_below_deemed(self):
        """
        1回目: 発電100, 売電10 → 自家消費90
        2〜6回目: みなし6×30=180ずつ（合計900）
        7回目: 発電150, 売電20 → 自家消費(50-10)=40
        調整: actual=(150-20)-(100-10)=130-90=40, billed=90+900+40=1030 → 調整=-990
        """
        bs1 = make_billing_summary(
            self.meter, date(2025, 1, 10), date(2025, 2, 10),
            Decimal('90'), 'none',
            curr_used_import=Decimal('100'), curr_used_export=Decimal('10'),
            is_first_billing=True,
        )
        prev = bs1
        months = [
            (date(2025, 2, 10), date(2025, 3, 10)),
            (date(2025, 3, 10), date(2025, 4, 10)),
            (date(2025, 4, 10), date(2025, 5, 10)),
            (date(2025, 5, 10), date(2025, 6, 10)),
            (date(2025, 6, 10), date(2025, 7, 10)),
        ]
        for start, end in months:
            prev = make_billing_summary(
                self.meter, start, end,
                Decimal('180'), 'monthly',
                curr_used_import=Decimal('100'), curr_used_export=Decimal('10'),
            )

        result7 = calculate_billing(
            meter=self.meter,
            prev_billing=prev,
            prev_import=None,
            prev_export=None,
            curr_import=Decimal('150'),
            curr_export=Decimal('20'),
            period_start=date(2025, 7, 10),
            period_end=date(2025, 8, 10),
        )
        self.assertEqual(result7['total_kwh'], Decimal('40'))

        from django.db.models import Sum
        past_total = BillingSummary.objects.filter(
            meter=self.meter,
            period_end__lte=date(2025, 7, 10),
        ).aggregate(total=Sum('total_kwh'))['total'] or Decimal('0')

        first_billing = BillingSummary.objects.get(meter=self.meter, is_first_billing=True)
        actual_cumulative = (
            result7['curr_used_import'] - result7['curr_used_export']
        ) - (
            first_billing.curr_used_import - first_billing.curr_used_export
        )
        billed_cumulative = past_total + result7['total_kwh']
        adjustment = actual_cumulative - billed_cumulative

        self.assertEqual(adjustment, Decimal('-990'))

    # =========================================================
    # ケース9: 売電量が大きく自家消費がゼロになるケース
    # =========================================================
    def test_case9_zero_self_consumption(self):
        """
        発電増分100, 売電増分150 → 自家消費=max(0, -50)=0
        """
        bs1 = make_billing_summary(
            self.meter, date(2026, 1, 10), date(2026, 2, 10),
            Decimal('0'), 'none',
            curr_used_import=Decimal('500'), curr_used_export=Decimal('200'),
            is_first_billing=True,
        )

        result2 = calculate_billing(
            meter=self.meter,
            prev_billing=bs1,
            prev_import=Decimal('500'),
            prev_export=Decimal('200'),
            curr_import=Decimal('600'),
            curr_export=Decimal('350'),
            period_start=date(2026, 2, 10),
            period_end=date(2026, 3, 10),
        )
        self.assertEqual(result2['total_kwh'], Decimal('0'))
        self.assertEqual(result2['deemed_method'], 'none')

    # =========================================================
    # ケース10: みなし日次単価が6kWh/日を上回るケース
    # =========================================================
    def test_case10_high_daily_avg(self):
        """
        直近12ヶ月の実測平均が20kWh/日の場合、みなしは20×日数になる
        """
        # 直近12ヶ月の実測データを作成（1ヶ月30日、600kWh=20kWh/日）
        for i in range(3):
            start = date(2025, 1 + i, 10)
            end = date(2025, 2 + i, 10)
            make_billing_summary(
                self.meter, start, end,
                Decimal('600'), 'none',
                curr_used_import=Decimal(str(500 + i * 600)),
                curr_used_export=Decimal('0'),
                is_first_billing=(i == 0),
            )

        deemed_daily = get_deemed_daily_kwh(self.meter, date(2025, 4, 10))
        self.assertGreater(deemed_daily, Decimal('6.0'))

        days = 30
        result = calculate_billing(
            meter=self.meter,
            prev_billing=BillingSummary.objects.filter(meter=self.meter).order_by('-period_end').first(),
            prev_import=None,
            prev_export=None,
            curr_import=None,
            curr_export=None,
            period_start=date(2025, 4, 10),
            period_end=date(2025, 5, 10),
            deemed_daily_kwh=deemed_daily,
        )
        self.assertEqual(result['deemed_method'], 'monthly')
        self.assertEqual(result['total_kwh'], deemed_daily * days)
        self.assertGreater(result['total_kwh'], Decimal('6.0') * days)