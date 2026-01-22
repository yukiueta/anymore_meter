from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import random

from app.meters.models import Meter, MeterAssignment
from app.readings.models import MeterReading, DailySummary, MonthlySummary
from app.billing.models import BillingCalendar, BillingSummary


class Command(BaseCommand):
    help = 'サンプルデータを生成'

    def add_arguments(self, parser):
        parser.add_argument(
            '--months',
            type=int,
            default=3,
            help='生成する月数（デフォルト: 3）',
        )
        parser.add_argument(
            '--meter-id',
            type=str,
            default='SAMPLE-001',
            help='メーターID（デフォルト: SAMPLE-001）',
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
        parser.add_argument(
            '--project-id',
            type=int,
            default=1001,
            help='案件ID（デフォルト: 1001）',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='既存のサンプルデータを削除してから生成',
        )

    def handle(self, *args, **options):
        months = options['months']
        meter_id = options['meter_id']
        zone = options['zone']
        base_billing_day = options['base_billing_day']
        project_id = options['project_id']
        clear = options['clear']

        self.stdout.write(f'サンプルデータ生成開始')
        self.stdout.write(f'  メーター: {meter_id}')
        self.stdout.write(f'  期間: {months}ヶ月')
        self.stdout.write(f'  電力管轄: {zone}')
        self.stdout.write(f'  基準検針日: {base_billing_day}')

        # 1. メーター作成または取得
        meter, created = Meter.objects.get_or_create(
            meter_id=meter_id,
            defaults={
                'status': 'active',
                'registered_at': timezone.now() - timedelta(days=months * 30),
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'メーター作成: {meter_id}'))
        else:
            self.stdout.write(f'既存メーター使用: {meter_id}')

        # クリアオプション
        if clear:
            self.clear_sample_data(meter)

        # 2. MeterAssignment作成
        assignment, created = MeterAssignment.objects.get_or_create(
            meter=meter,
            end_date__isnull=True,
            defaults={
                'project_id': project_id,
                'project_name': f'サンプル案件{project_id}',
                'zone': zone,
                'base_billing_day': base_billing_day,
                'start_date': timezone.now().date() - timedelta(days=months * 30),
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'紐付け作成: project_id={project_id}'))
        else:
            # 既存のassignmentを更新
            assignment.zone = zone
            assignment.base_billing_day = base_billing_day
            assignment.save()
            self.stdout.write(f'既存紐付け更新')

        # 3. 30分データ生成
        readings_count = self.generate_readings(meter, months)
        self.stdout.write(self.style.SUCCESS(f'30分データ生成: {readings_count}件'))

        # 4. 日次サマリー生成
        daily_count = self.generate_daily_summaries(meter, months)
        self.stdout.write(self.style.SUCCESS(f'日次サマリー生成: {daily_count}件'))

        # 5. 月次サマリー生成
        monthly_count = self.generate_monthly_summaries(meter, months)
        self.stdout.write(self.style.SUCCESS(f'月次サマリー生成: {monthly_count}件'))

        # 6. 請求データ生成
        billing_count = self.generate_billing_summaries(meter, assignment, months)
        self.stdout.write(self.style.SUCCESS(f'請求データ生成: {billing_count}件'))

        self.stdout.write(self.style.SUCCESS('サンプルデータ生成完了'))

    def clear_sample_data(self, meter):
        """既存のサンプルデータを削除"""
        MeterReading.objects.filter(meter=meter).delete()
        DailySummary.objects.filter(meter=meter).delete()
        MonthlySummary.objects.filter(meter=meter).delete()
        BillingSummary.objects.filter(meter=meter).delete()
        self.stdout.write(self.style.WARNING('既存データ削除完了'))

    def generate_readings(self, meter, months):
        """30分データを生成"""
        now = timezone.now()
        start_date = now - timedelta(days=months * 30)
        
        readings = []
        current_time = start_date.replace(minute=0, second=0, microsecond=0)
        
        # 累計値の初期値
        import_kwh = Decimal('1000.00')
        export_kwh = Decimal('500.00')
        route_b_import_kwh = Decimal('2000.00')
        route_b_export_kwh = Decimal('300.00')
        
        while current_time < now:
            # 30分ごとの発電量（時間帯で変動）
            hour = current_time.hour
            if 6 <= hour <= 18:  # 日中
                generation = Decimal(random.uniform(0.5, 2.0))
            else:  # 夜間
                generation = Decimal('0.00')
            
            # 自家消費と売電
            consumption = Decimal(random.uniform(0.3, 1.0))
            if generation > consumption:
                sold = generation - consumption
                bought = Decimal('0.00')
            else:
                sold = Decimal('0.00')
                bought = consumption - generation
            
            import_kwh += generation
            export_kwh += consumption
            route_b_import_kwh += bought
            route_b_export_kwh += sold
            
            readings.append(MeterReading(
                meter=meter,
                timestamp=current_time,
                reading_type='interval',
                import_kwh=round(import_kwh, 2),
                export_kwh=round(export_kwh, 2),
                route_b_import_kwh=round(route_b_import_kwh, 2),
                route_b_export_kwh=round(route_b_export_kwh, 2),
            ))
            
            current_time += timedelta(minutes=30)
            
            # バッチ挿入（メモリ節約）
            if len(readings) >= 1000:
                MeterReading.objects.bulk_create(readings, ignore_conflicts=True)
                readings = []
        
        if readings:
            MeterReading.objects.bulk_create(readings, ignore_conflicts=True)
        
        return MeterReading.objects.filter(meter=meter).count()

    def generate_daily_summaries(self, meter, months):
        """日次サマリーを生成"""
        now = timezone.now()
        start_date = (now - timedelta(days=months * 30)).date()
        
        summaries = []
        current_date = start_date
        
        while current_date < now.date():
            generation = Decimal(random.uniform(5.0, 25.0))
            export = Decimal(random.uniform(1.0, 10.0))
            self_consumption = generation - export
            grid_import = Decimal(random.uniform(2.0, 8.0))
            
            summaries.append(DailySummary(
                meter=meter,
                date=current_date,
                generation_kwh=round(generation, 2),
                export_kwh=round(export, 2),
                self_consumption_kwh=round(self_consumption, 2),
                grid_import_kwh=round(grid_import, 2),
                record_count=48,
            ))
            
            current_date += timedelta(days=1)
        
        DailySummary.objects.bulk_create(summaries, ignore_conflicts=True)
        return len(summaries)

    def generate_monthly_summaries(self, meter, months):
        """月次サマリーを生成"""
        now = timezone.now()
        
        summaries = []
        for i in range(months):
            target_date = now - timedelta(days=30 * i)
            year_month = target_date.strftime('%Y-%m')
            
            days_in_month = 30
            generation = Decimal(random.uniform(150.0, 600.0))
            export = Decimal(random.uniform(50.0, 250.0))
            self_consumption = generation - export
            grid_import = Decimal(random.uniform(80.0, 200.0))
            
            summaries.append(MonthlySummary(
                meter=meter,
                year_month=year_month,
                generation_kwh=round(generation, 2),
                export_kwh=round(export, 2),
                self_consumption_kwh=round(self_consumption, 2),
                grid_import_kwh=round(grid_import, 2),
            ))
        
        MonthlySummary.objects.bulk_create(summaries, ignore_conflicts=True)
        return len(summaries)

    def generate_billing_summaries(self, meter, assignment, months):
        """請求データを生成"""
        now = timezone.now()
        zone = assignment.zone
        base_billing_day = assignment.base_billing_day
        
        # BillingCalendarから検針日を取得
        calendars = BillingCalendar.objects.filter(
            zone=zone,
            base_billing_day=base_billing_day,
            actual_billing_date__lte=now.date(),
            actual_billing_date__gte=now.date() - timedelta(days=months * 30)
        ).order_by('actual_billing_date')
        
        if not calendars.exists():
            self.stdout.write(self.style.WARNING(
                f'BillingCalendarが見つかりません（zone={zone}, base_billing_day={base_billing_day}）'
            ))
            # カレンダーがない場合は手動で期間を作成
            return self.generate_billing_summaries_manual(meter, assignment, months)
        
        summaries = []
        prev_calendar = None
        
        # 累計値
        import_kwh = Decimal('1000.00')
        route_b_export_kwh = Decimal('300.00')
        
        for calendar in calendars:
            if prev_calendar is None:
                prev_calendar = calendar
                continue
            
            period_start = prev_calendar.actual_billing_date
            period_end = calendar.actual_billing_date
            
            # 期間の発電量
            generation = Decimal(random.uniform(150.0, 500.0))
            sold = Decimal(random.uniform(50.0, 200.0))
            self_consumption = generation - sold
            
            import_start = import_kwh
            import_end = import_kwh + generation
            route_b_export_start = route_b_export_kwh
            route_b_export_end = route_b_export_kwh + sold
            
            summaries.append(BillingSummary(
                meter=meter,
                project_id=assignment.project_id,
                project_name=assignment.project_name,
                zone=zone,
                base_billing_day=base_billing_day,
                period_start=period_start,
                period_end=period_end,
                import_start=round(import_start, 2),
                import_end=round(import_end, 2),
                route_b_export_start=round(route_b_export_start, 2),
                route_b_export_end=round(route_b_export_end, 2),
                generation_kwh=round(generation, 2),
                sold_kwh=round(sold, 2),
                self_consumption_kwh=round(self_consumption, 2),
                data_missing=False,
            ))
            
            import_kwh = import_end
            route_b_export_kwh = route_b_export_end
            prev_calendar = calendar
        
        BillingSummary.objects.bulk_create(summaries, ignore_conflicts=True)
        return len(summaries)

    def generate_billing_summaries_manual(self, meter, assignment, months):
        """BillingCalendarがない場合の請求データ生成"""
        now = timezone.now()
        base_day = int(assignment.base_billing_day)
        
        summaries = []
        import_kwh = Decimal('1000.00')
        route_b_export_kwh = Decimal('300.00')
        
        for i in range(months - 1, 0, -1):
            # 検針期間を計算
            end_date = now.date() - timedelta(days=30 * (i - 1))
            end_date = end_date.replace(day=min(base_day, 28))
            start_date = end_date - timedelta(days=30)
            
            generation = Decimal(random.uniform(150.0, 500.0))
            sold = Decimal(random.uniform(50.0, 200.0))
            self_consumption = generation - sold
            
            import_start = import_kwh
            import_end = import_kwh + generation
            route_b_export_start = route_b_export_kwh
            route_b_export_end = route_b_export_kwh + sold
            
            summaries.append(BillingSummary(
                meter=meter,
                project_id=assignment.project_id,
                project_name=assignment.project_name,
                zone=assignment.zone,
                base_billing_day=assignment.base_billing_day,
                period_start=start_date,
                period_end=end_date,
                import_start=round(import_start, 2),
                import_end=round(import_end, 2),
                route_b_export_start=round(route_b_export_start, 2),
                route_b_export_end=round(route_b_export_end, 2),
                generation_kwh=round(generation, 2),
                sold_kwh=round(sold, 2),
                self_consumption_kwh=round(self_consumption, 2),
                data_missing=False,
            ))
            
            import_kwh = import_end
            route_b_export_kwh = route_b_export_end
        
        BillingSummary.objects.bulk_create(summaries, ignore_conflicts=True)
        return len(summaries)