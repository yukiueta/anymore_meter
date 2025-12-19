from celery import shared_task
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from .models import MeterReading, DailySummary, MonthlySummary
from app.meters.models import Meter


@shared_task
def aggregate_daily(target_date=None):
    if target_date is None:
        target_date = (timezone.now() - timedelta(days=1)).date()

    meters = Meter.objects.filter(is_deleted=False)

    for meter in meters:
        readings = MeterReading.objects.filter(
            meter=meter,
            recorded_at__date=target_date
        ).aggregate(
            total_import=Sum('import_kwh'),
            total_export=Sum('export_kwh'),
            total_pv=Sum('pv_energy_kwh'),
            count=Count('id')
        )

        DailySummary.objects.update_or_create(
            meter=meter,
            date=target_date,
            defaults={
                'total_import_kwh': readings['total_import'],
                'total_export_kwh': readings['total_export'],
                'total_pv_kwh': readings['total_pv'],
                'record_count': readings['count'],
            }
        )


@shared_task
def aggregate_monthly(target_year_month=None):
    if target_year_month is None:
        last_month = timezone.now().replace(day=1) - timedelta(days=1)
        target_year_month = last_month.strftime('%Y-%m')

    meters = Meter.objects.filter(is_deleted=False)

    for meter in meters:
        summaries = DailySummary.objects.filter(
            meter=meter,
            date__startswith=target_year_month
        ).aggregate(
            total_import=Sum('total_import_kwh'),
            total_export=Sum('total_export_kwh'),
            total_pv=Sum('total_pv_kwh'),
        )

        MonthlySummary.objects.update_or_create(
            meter=meter,
            year_month=target_year_month,
            defaults={
                'total_import_kwh': summaries['total_import'],
                'total_export_kwh': summaries['total_export'],
                'total_pv_kwh': summaries['total_pv'],
            }
        )