from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import random
import calendar as cal

from app.meters.models import Meter, MeterAssignment
from app.readings.models import MeterReading, DailySummary, MonthlySummary
from app.billing.models import BillingCalendar, BillingSummary

DEEMED_DAILY_KWH = Decimal('6.0')
DEEMED_MONTHLY_KWH = Decimal('180.0')


class Command(BaseCommand):
    help = '請求用サンプルデータを生成（Anymore案件連携テスト用）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--months',
            type=int,
            default=3,
            help='生成する月数（デフォルト: 3）',
        )
        parser.add_argument(
            '--zone',
            type=int,
            default=3,
            help='電力管轄（デフォルト: 3=東京電力）',
        )
        parser.add_argument(
            '--base-billing-day',
            type=str,
            default='05',
            help='基準検針日（デフォルト: 05）',
        )

    def handle(self, *args, **options):
        months = options['months']
        zone = options['zone']
        base_billing_day = options['base_billing_day']

        self.stdout.write(self.style.WARNING('=== 全データ削除 ==='))
        self.clear_all_data()

        self.stdout.write(f'\n=== サンプルデータ生成 ===')
        self.stdout.write(f'  期間: {months}ヶ月')
        self.stdout.write(f'  電力管轄: {zone}')
        self.stdout.write(f'  基準検針日: {base_billing_day}')

        # 検針カレンダーを確認/作成
        calendars = self.ensure_billing_calendars(zone, base_billing_day, months)
        self.stdout.write(self.style.SUCCESS(f'\n検針カレンダー: {len(calendars)}件'))

        # Anymore案件IDとパターンの対応
        test_cases = [
            {
                'project_id': 23546,
                'meter_id': 'TGO-METER-001',
                'pattern': 'normal',
                'description': '正常：全データあり（実測計算）',
            },
            {
                'project_id': 23537,
                'meter_id': 'TGO-METER-002',
                'pattern': 'first_only',
                'description': '初回：最初の期間は前回データなし',
            },
            {
                'project_id': 23525,
                'meter_id': 'TGO-METER-003',
                'pattern': 'daily_deemed',
                'description': '日次みなし：今回欠損、期間中あり（6kWh/日）',
            },
            {
                'project_id': 23499,
                'meter_id': 'TGO-METER-004',
                'pattern': 'monthly_deemed',
                'description': '月次みなし：今回・期間中欠損（180kWh/月）',
            },
            {
                'project_id': 23486,
                'meter_id': 'TGO-METER-005',
                'pattern': 'never_received',
                'description': '未受信：一度もデータなし（全期間180kWh/月）',
            },
        ]

        for case in test_cases:
            self.stdout.write(f'\n--- {case["description"]} ---')
            self.stdout.write(f'  案件ID: {case["project_id"]}')
            self.stdout.write(f'  メーターID: {case["meter_id"]}')

            meter = self.create_meter(
                meter_id=case['meter_id'],
                project_id=case['project_id'],
                zone=zone,
                base_billing_day=base_billing_day
            )
            self.generate_readings_for_pattern(meter, calendars, case['pattern'])
            self.generate_daily_summaries(meter)
            self.generate_monthly_summaries(meter)
            self.generate_billing_summaries(meter, calendars, case['pattern'])

        self.stdout.write(self.style.SUCCESS('\n=== サンプルデータ生成完了 ==='))
        self.print_summary()

    def clear_all_data(self):
        """全データを削除"""
        deleted_billing = BillingSummary.objects.all().delete()[0]
        deleted_monthly = MonthlySummary.objects.all().delete()[0]
        deleted_daily = DailySummary.objects.all().delete()[0]
        deleted_readings = MeterReading.objects.all().delete()[0]
        deleted_assignment = MeterAssignment.objects.all().delete()[0]
        deleted_meters = Meter.objects.all().delete()[0]

        self.stdout.write(
            f'  メーター: {deleted_meters}件\n'
            f'  紐付け: {deleted_assignment}件\n'
            f'  30分データ: {deleted_readings}件\n'
            f'  日次集計: {deleted_daily}件\n'
            f'  月次集計: {deleted_monthly}件\n'
            f'  請求データ: {deleted_billing}件'
        )

    def ensure_billing_calendars(self, zone, base_billing_day, months):
        """検針カレンダーを確認/作成"""
        calendars = []
        now = timezone.now().date()

        for i in range(months + 1):
            target_date = now - timedelta(days=30 * i)
            year = target_date.year
            month = target_date.month
            fiscal_year = year if month >= 4 else year - 1

            billing_day = int(base_billing_day)
            try:
                billing_date = target_date.replace(day=billing_day)
            except ValueError:
                last_day = cal.monthrange(target_date.year, target_date.month)[1]
                billing_date = target_date.replace(day=last_day)

            calendar, created = BillingCalendar.objects.get_or_create(
                fiscal_year=fiscal_year,
                month=month,
                zone=zone,
                base_billing_day=base_billing_day,
                defaults={'actual_billing_date': billing_date}
            )
            calendars.append(calendar)

        return sorted(calendars, key=lambda x: x.actual_billing_date)

    def create_meter(self, meter_id, project_id, zone, base_billing_day):
        """メーターと紐付けを作成"""
        meter = Meter.objects.create(
            meter_id=meter_id,
            status='active',
            registered_at=timezone.now() - timedelta(days=120),
        )
        self.stdout.write(f'  メーター作成: {meter_id}')

        MeterAssignment.objects.create(
            meter=meter,
            project_id=project_id,
            project_name=f'Anymore案件 #{project_id}',
            zone=zone,
            base_billing_day=base_billing_day,
            start_date=timezone.now().date() - timedelta(days=120),
        )

        return meter

    def generate_readings_for_pattern(self, meter, calendars, pattern):
        """パターンに応じた30分データを生成"""
        if pattern == 'never_received':
            self.stdout.write(f'  30分データ: 0件（未受信パターン）')
            return

        readings = []
        import_kwh = Decimal('1000.00')

        start_date = calendars[0].actual_billing_date
        end_date = calendars[-1].actual_billing_date + timedelta(days=1)

        current_time = timezone.make_aware(
            datetime.combine(start_date, datetime.min.time())
        )
        end_time = timezone.make_aware(
            datetime.combine(end_date, datetime.min.time())
        )

        # パターン判定用の日付
        first_period_end = calendars[1].actual_billing_date if len(calendars) > 1 else end_date
        latest_period_start = calendars[-2].actual_billing_date if len(calendars) >= 2 else start_date
        latest_period_end = calendars[-1].actual_billing_date

        while current_time < end_time:
            current_date = current_time.date()
            skip = False

            if pattern == 'first_only':
                # 最初の検針期間のデータをスキップ
                if current_date < first_period_end:
                    skip = True

            elif pattern == 'daily_deemed':
                # 最新期間の最後7日間をスキップ
                if current_date >= latest_period_end - timedelta(days=7):
                    skip = True

            elif pattern == 'monthly_deemed':
                # 最新期間の全データをスキップ
                if current_date >= latest_period_start:
                    skip = True

            if not skip:
                hour = current_time.hour
                if 6 <= hour <= 18:
                    generation = Decimal(random.uniform(0.3, 1.5))
                else:
                    generation = Decimal('0.00')

                import_kwh += generation

                readings.append(MeterReading(
                    meter=meter,
                    timestamp=current_time,
                    reading_type='interval',
                    import_kwh=round(import_kwh, 2),
                    export_kwh=Decimal('0'),
                    route_b_import_kwh=Decimal('0'),
                    route_b_export_kwh=Decimal('0'),
                ))

            current_time += timedelta(minutes=30)

            if len(readings) >= 2000:
                MeterReading.objects.bulk_create(readings, ignore_conflicts=True)
                readings = []

        if readings:
            MeterReading.objects.bulk_create(readings, ignore_conflicts=True)

        count = MeterReading.objects.filter(meter=meter).count()
        self.stdout.write(f'  30分データ: {count}件')

    def generate_daily_summaries(self, meter):
        """日次集計を生成"""
        from django.db.models import Sum, Count, Min, Max
        from django.db.models.functions import TruncDate

        readings = MeterReading.objects.filter(meter=meter)
        if not readings.exists():
            self.stdout.write(f'  日次集計: 0件')
            return

        daily_data = readings.annotate(
            date=TruncDate('timestamp')
        ).values('date').annotate(
            min_import=Min('import_kwh'),
            max_import=Max('import_kwh'),
            count=Count('id')
        ).order_by('date')

        summaries = []
        for d in daily_data:
            generation = d['max_import'] - d['min_import'] if d['max_import'] and d['min_import'] else Decimal('0')
            summaries.append(DailySummary(
                meter=meter,
                date=d['date'],
                generation_kwh=generation,
                export_kwh=Decimal('0'),
                self_consumption_kwh=generation,
                grid_import_kwh=Decimal('0'),
                record_count=d['count']
            ))

        DailySummary.objects.bulk_create(summaries)
        self.stdout.write(f'  日次集計: {len(summaries)}件')

    def generate_monthly_summaries(self, meter):
        """月次集計を生成"""
        from django.db.models import Sum
        from django.db.models.functions import TruncMonth

        daily_summaries = DailySummary.objects.filter(meter=meter)
        if not daily_summaries.exists():
            self.stdout.write(f'  月次集計: 0件')
            return

        monthly_data = daily_summaries.annotate(
            month=TruncMonth('date')
        ).values('month').annotate(
            total_generation=Sum('generation_kwh'),
            total_export=Sum('export_kwh'),
            total_self_consumption=Sum('self_consumption_kwh'),
            total_grid_import=Sum('grid_import_kwh')
        ).order_by('month')

        summaries = []
        for m in monthly_data:
            year_month = m['month'].strftime('%Y-%m')
            summaries.append(MonthlySummary(
                meter=meter,
                year_month=year_month,
                generation_kwh=m['total_generation'] or Decimal('0'),
                export_kwh=m['total_export'] or Decimal('0'),
                self_consumption_kwh=m['total_self_consumption'] or Decimal('0'),
                grid_import_kwh=m['total_grid_import'] or Decimal('0')
            ))

        MonthlySummary.objects.bulk_create(summaries)
        self.stdout.write(f'  月次集計: {len(summaries)}件')

    def generate_billing_summaries(self, meter, calendars, pattern):
        """請求データを生成"""
        assignment = MeterAssignment.objects.filter(
            meter=meter,
            end_date__isnull=True
        ).first()

        if not assignment:
            self.stdout.write(self.style.ERROR('  紐付けが見つかりません'))
            return

        count = 0
        prev_used_value = Decimal('0')

        for i in range(len(calendars) - 1):
            period_start = calendars[i].actual_billing_date
            period_end = calendars[i + 1].actual_billing_date
            is_first = (i == 0)

            result = self.calculate_billing(
                meter=meter,
                prev_used_value=prev_used_value,
                period_start=period_start,
                period_end=period_end,
                is_first=is_first
            )

            BillingSummary.objects.create(
                meter=meter,
                project_id=assignment.project_id,
                project_name=assignment.project_name,
                zone=assignment.zone,
                base_billing_day=assignment.base_billing_day,
                period_start=period_start,
                period_end=period_end,
                **result
            )

            prev_used_value = result['curr_used_value']
            count += 1

            method = result['deemed_method']
            total = result['total_kwh']
            self.stdout.write(
                f'  請求: {period_start}〜{period_end} '
                f'total={total}kWh method={method}'
            )

        self.stdout.write(f'  請求データ: {count}件')

    def calculate_billing(self, meter, prev_used_value, period_start, period_end, is_first):
        """請求データを計算"""
        prev_reading = MeterReading.objects.filter(
            meter=meter,
            timestamp__date=period_start
        ).order_by('-timestamp').first()

        curr_reading = MeterReading.objects.filter(
            meter=meter,
            timestamp__date=period_end
        ).order_by('-timestamp').first()

        mid_reading = MeterReading.objects.filter(
            meter=meter,
            timestamp__date__gt=period_start,
            timestamp__date__lt=period_end
        ).order_by('-timestamp').first()

        prev_actual = Decimal(str(prev_reading.import_kwh)) if prev_reading else None
        curr_actual = Decimal(str(curr_reading.import_kwh)) if curr_reading else None

        result = {
            'prev_actual_value': prev_actual,
            'curr_actual_value': curr_actual,
            'mid_actual_value': None,
            'mid_actual_date': None,
            'prev_used_value': Decimal('0'),
            'curr_used_value': Decimal('0'),
            'actual_kwh': Decimal('0'),
            'deemed_kwh': Decimal('0'),
            'total_kwh': Decimal('0'),
            'deemed_method': 'none',
            'is_first_billing': is_first,
            'note': ''
        }

        # 前回値を決定
        if is_first:
            result['prev_used_value'] = Decimal('0')
        elif prev_actual is not None:
            result['prev_used_value'] = prev_actual
        else:
            result['prev_used_value'] = prev_used_value

        # パターン判定
        if curr_actual is not None:
            # 実測可能
            result['curr_used_value'] = curr_actual
            result['actual_kwh'] = curr_actual - result['prev_used_value']
            result['deemed_kwh'] = Decimal('0')
            result['total_kwh'] = result['actual_kwh']
            result['deemed_method'] = 'none'

            if is_first:
                result['note'] = '初回検針（前回値0基準）'

        elif mid_reading:
            # 日次みなし
            mid_actual = Decimal(str(mid_reading.import_kwh))
            mid_date = mid_reading.timestamp.date()

            result['mid_actual_value'] = mid_actual
            result['mid_actual_date'] = mid_date

            actual_kwh = mid_actual - result['prev_used_value']
            remaining_days = (period_end - mid_date).days
            deemed_kwh = DEEMED_DAILY_KWH * remaining_days

            result['curr_used_value'] = mid_actual + deemed_kwh
            result['actual_kwh'] = actual_kwh
            result['deemed_kwh'] = deemed_kwh
            result['total_kwh'] = actual_kwh + deemed_kwh
            result['deemed_method'] = 'daily'
            result['note'] = f'期間中最新({mid_date})以降は6kWh/日×{remaining_days}日'

        else:
            # 月次みなし
            result['curr_used_value'] = result['prev_used_value'] + DEEMED_MONTHLY_KWH
            result['actual_kwh'] = Decimal('0')
            result['deemed_kwh'] = DEEMED_MONTHLY_KWH
            result['total_kwh'] = DEEMED_MONTHLY_KWH
            result['deemed_method'] = 'monthly'
            result['note'] = '180kWh/月でみなし計算'

        return result

    def print_summary(self):
        """サマリーを出力"""
        self.stdout.write('\n=== データサマリー ===')
        self.stdout.write(f'メーター: {Meter.objects.count()}件')
        self.stdout.write(f'紐付け: {MeterAssignment.objects.count()}件')
        self.stdout.write(f'30分データ: {MeterReading.objects.count()}件')
        self.stdout.write(f'日次集計: {DailySummary.objects.count()}件')
        self.stdout.write(f'月次集計: {MonthlySummary.objects.count()}件')
        self.stdout.write(f'請求データ: {BillingSummary.objects.count()}件')

        self.stdout.write('\n=== 案件別請求データ ===')
        from django.db.models import Sum
        billing_by_project = BillingSummary.objects.values(
            'project_id', 'project_name'
        ).annotate(
            total_actual=Sum('actual_kwh'),
            total_deemed=Sum('deemed_kwh'),
            total_kwh=Sum('total_kwh')
        ).order_by('project_id')

        for b in billing_by_project:
            self.stdout.write(
                f'  #{b["project_id"]} {b["project_name"]}: '
                f'実測={b["total_actual"]}kWh みなし={b["total_deemed"]}kWh 合計={b["total_kwh"]}kWh'
            )