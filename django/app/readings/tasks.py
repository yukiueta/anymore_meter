# django/app/readings/tasks.py
from celery import shared_task
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta, date
from decimal import Decimal
import logging

from .models import MeterReading, DailySummary, MonthlySummary
from app.meters.models import Meter

logger = logging.getLogger(__name__)


@shared_task
def aggregate_daily(target_date=None):
    """
    日次集計（毎日AM1:00実行）
    MeterReadingは累積値なので、差分で当日の増分を計算
    """
    if target_date is None:
        target_date = (timezone.now() - timedelta(days=1)).date()
    elif isinstance(target_date, str):
        target_date = date.fromisoformat(target_date)

    logger.info(f'Daily aggregation started for {target_date}')

    # 対象日にデータがあるメーターのみ処理
    meter_ids = MeterReading.objects.filter(
        timestamp__date=target_date
    ).values_list('meter_id', flat=True).distinct()

    meters = Meter.objects.filter(id__in=meter_ids, is_deleted=False)
    count = 0

    for meter in meters:
        if _aggregate_daily_for_meter(meter, target_date):
            count += 1

    logger.info(f'Daily aggregation completed: {count} meters')
    return {'count': count, 'date': str(target_date)}


def _aggregate_daily_for_meter(meter, target_date):
    """メーター単位の日次集計"""
    # 当日の最後のレコード
    last_reading = MeterReading.objects.filter(
        meter=meter,
        timestamp__date=target_date
    ).order_by('-timestamp').first()

    if not last_reading:
        return False

    # 前日の最後のレコード（差分計算用）
    prev_reading = MeterReading.objects.filter(
        meter=meter,
        timestamp__date__lt=target_date
    ).order_by('-timestamp').first()

    # 当日のレコード数
    record_count = MeterReading.objects.filter(
        meter=meter,
        timestamp__date=target_date
    ).count()

    # 差分計算（累積値から増分を算出）
    def delta(curr, prev, field):
        curr_val = getattr(curr, field) if curr else None
        prev_val = getattr(prev, field) if prev else None
        if curr_val is None:
            return None
        if prev_val is None:
            return curr_val  # 初回は累積値そのまま
        d = curr_val - prev_val
        return max(d, Decimal('0'))

    generation_kwh = delta(last_reading, prev_reading, 'import_kwh')
    export_kwh = delta(last_reading, prev_reading, 'route_b_export_kwh')
    grid_import_kwh = delta(last_reading, prev_reading, 'route_b_import_kwh')

    # 自家消費量 = 発電量 - 売電量
    self_consumption_kwh = None
    if generation_kwh is not None:
        if export_kwh is not None:
            self_consumption_kwh = max(generation_kwh - export_kwh, Decimal('0'))
        else:
            self_consumption_kwh = generation_kwh

    DailySummary.objects.update_or_create(
        meter=meter,
        date=target_date,
        defaults={
            'generation_kwh': generation_kwh,
            'export_kwh': export_kwh,
            'self_consumption_kwh': self_consumption_kwh,
            'grid_import_kwh': grid_import_kwh,
            'record_count': record_count,
        }
    )
    return True


@shared_task
def aggregate_monthly(target_year_month=None):
    """
    月次集計（毎月1日AM2:00実行）
    DailySummaryを合算
    """
    if target_year_month is None:
        last_month = timezone.now().replace(day=1) - timedelta(days=1)
        target_year_month = last_month.strftime('%Y-%m')

    year, month = map(int, target_year_month.split('-'))
    logger.info(f'Monthly aggregation started for {target_year_month}')

    meter_ids = DailySummary.objects.filter(
        date__year=year,
        date__month=month
    ).values_list('meter_id', flat=True).distinct()

    meters = Meter.objects.filter(id__in=meter_ids, is_deleted=False)
    count = 0

    for meter in meters:
        result = DailySummary.objects.filter(
            meter=meter,
            date__year=year,
            date__month=month
        ).aggregate(
            generation=Sum('generation_kwh'),
            export=Sum('export_kwh'),
            self_consumption=Sum('self_consumption_kwh'),
            grid_import=Sum('grid_import_kwh'),
        )

        MonthlySummary.objects.update_or_create(
            meter=meter,
            year_month=target_year_month,
            defaults={
                'generation_kwh': result['generation'],
                'export_kwh': result['export'],
                'self_consumption_kwh': result['self_consumption'],
                'grid_import_kwh': result['grid_import'],
            }
        )
        count += 1

    logger.info(f'Monthly aggregation completed: {count} meters')
    return {'count': count, 'year_month': target_year_month}