from django.core.management.base import BaseCommand
from datetime import datetime, timedelta, date
from decimal import Decimal
import random
from django.db.models import Sum, Count
from django.db.models.functions import TruncDate, TruncMonth

from app.meters.models import Meter, MeterAssignment
from app.readings.models import MeterReading, DailySummary, MonthlySummary


class Command(BaseCommand):
    help = 'テスト用ダミーデータを作成'

    def add_arguments(self, parser):
        parser.add_argument(
            '--meter-id',
            type=str,
            default='TEST-METER-001',
            help='メーターID'
        )
        parser.add_argument(
            '--project-id',
            type=str,
            required=True,
            help='Anymore側のproject_id（例: TEST-00021040）'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=90,
            help='何日分のデータを作成するか'
        )

    def handle(self, *args, **options):
        meter_id = options['meter_id']
        project_id = options['project_id']
        days = options['days']

        self.stdout.write(f"メーターID: {meter_id}")
        self.stdout.write(f"案件ID: {project_id}")
        self.stdout.write(f"データ期間: {days}日分")

        # 1. メーター作成
        meter, created = Meter.objects.get_or_create(
            meter_id=meter_id,
            defaults={
                'status': 'active',
                'last_received_at': datetime.now()
            }
        )
        self.stdout.write(self.style.SUCCESS(f"Meter: {meter.meter_id} (created: {created})"))

        # 2. 案件紐付け
        assignment, created = MeterAssignment.objects.get_or_create(
            meter=meter,
            project_id=project_id,
            defaults={
                'start_date': date.today() - timedelta(days=days)
            }
        )
        self.stdout.write(self.style.SUCCESS(f"Assignment: {assignment} (created: {created})"))

        # 3. 過去N日分の30分データ作成
        start_date = datetime.now() - timedelta(days=days)
        current = start_date

        readings_to_create = []
        while current <= datetime.now():
            hour = current.hour
            
            # 日中（6-18時）は発電あり
            if 6 <= hour <= 18:
                pv = Decimal(str(round(random.uniform(0.5, 3.0), 3)))
                export = Decimal(str(round(float(pv) * random.uniform(0.3, 0.7), 3)))
            else:
                pv = Decimal('0')
                export = Decimal('0')
            
            import_kwh = Decimal(str(round(random.uniform(0.1, 0.8), 3)))
            
            readings_to_create.append(MeterReading(
                meter=meter,
                recorded_at=current,
                import_kwh=import_kwh,
                export_kwh=export,
                pv_energy_kwh=pv,
                pyranometer=Decimal(str(round(random.uniform(0, 1000), 3))) if pv > 0 else Decimal('0')
            ))
            
            current += timedelta(minutes=30)

        # 既存データ削除して作り直し
        MeterReading.objects.filter(meter=meter).delete()
        MeterReading.objects.bulk_create(readings_to_create)
        self.stdout.write(self.style.SUCCESS(f"Created {len(readings_to_create)} readings"))

        # 4. 日次集計作成
        DailySummary.objects.filter(meter=meter).delete()
        
        daily_data = MeterReading.objects.filter(meter=meter).annotate(
            date=TruncDate('recorded_at')
        ).values('date').annotate(
            total_import=Sum('import_kwh'),
            total_export=Sum('export_kwh'),
            total_pv=Sum('pv_energy_kwh'),
            count=Count('id')
        )

        daily_summaries = []
        for d in daily_data:
            daily_summaries.append(DailySummary(
                meter=meter,
                date=d['date'],
                total_import_kwh=d['total_import'],
                total_export_kwh=d['total_export'],
                total_pv_kwh=d['total_pv'],
                record_count=d['count']
            ))
        DailySummary.objects.bulk_create(daily_summaries)
        self.stdout.write(self.style.SUCCESS(f"Created {len(daily_summaries)} daily summaries"))

        # 5. 月次集計作成
        MonthlySummary.objects.filter(meter=meter).delete()
        
        monthly_data = DailySummary.objects.filter(meter=meter).annotate(
            month=TruncMonth('date')
        ).values('month').annotate(
            total_import=Sum('total_import_kwh'),
            total_export=Sum('total_export_kwh'),
            total_pv=Sum('total_pv_kwh')
        )

        monthly_summaries = []
        for m in monthly_data:
            year_month = m['month'].strftime('%Y-%m')
            monthly_summaries.append(MonthlySummary(
                meter=meter,
                year_month=year_month,
                total_import_kwh=m['total_import'],
                total_export_kwh=m['total_export'],
                total_pv_kwh=m['total_pv']
            ))
        MonthlySummary.objects.bulk_create(monthly_summaries)
        self.stdout.write(self.style.SUCCESS(f"Created {len(monthly_summaries)} monthly summaries"))

        self.stdout.write(self.style.SUCCESS("Done!"))