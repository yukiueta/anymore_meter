# django/app/billing/tasks.py
"""
請求集計タスク

重要: PPA課金対象は自家消費量
  total_kwh = import_kwh - route_b_export_kwh（発電量 - 売電量）
  
  ※ import_kwh: パワコンからの発電量（累計値）
  ※ route_b_export_kwh: 系統への売電量（Bルート、累計値）
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import logging

from app.billing.models import BillingCalendar, BillingSummary
from app.meters.models import MeterAssignment
from app.readings.models import MeterReading

logger = logging.getLogger(__name__)

DEEMED_DAILY_KWH = Decimal('6.0')
DEEMED_MONTHLY_KWH = Decimal('180.0')


@shared_task
def generate_billing_summary(target_date=None):
    """
    請求集計を生成（検針日翌日に実行）
    target_date: YYYY-MM-DD形式。指定しない場合は昨日
    """
    if target_date:
        from datetime import datetime
        billing_date = datetime.strptime(target_date, '%Y-%m-%d').date()
    else:
        billing_date = timezone.now().date() - timedelta(days=1)
    
    logger.info(f'請求集計開始: 検針日={billing_date}')
    
    # 対象検針日のBillingCalendarを取得
    calendars = BillingCalendar.objects.filter(actual_billing_date=billing_date)
    
    if not calendars.exists():
        logger.info('対象の検針日がありません')
        return {'processed': 0, 'created': 0, 'errors': 0}
    
    results = {'processed': 0, 'created': 0, 'errors': 0}
    
    for calendar in calendars:
        result = process_calendar(calendar, billing_date)
        results['processed'] += result['processed']
        results['created'] += result['created']
        results['errors'] += result['errors']
    
    logger.info(f'請求集計完了: {results}')
    return results


def process_calendar(calendar, billing_date):
    """検針カレンダー単位で処理"""
    results = {'processed': 0, 'created': 0, 'errors': 0}
    
    # 該当するアクティブなMeterAssignmentを取得
    assignments = MeterAssignment.objects.filter(
        zone=calendar.zone,
        base_billing_day=calendar.base_billing_day,
        end_date__isnull=True
    ).select_related('meter')
    
    if not assignments.exists():
        return results
    
    # 前回検針日を取得
    prev_calendar = get_previous_billing_date(calendar)
    if not prev_calendar:
        logger.warning(f'前回検針日が見つかりません: zone={calendar.zone}, base_billing_day={calendar.base_billing_day}')
        return results
    
    prev_billing_date = prev_calendar.actual_billing_date
    
    for assignment in assignments:
        results['processed'] += 1
        try:
            created = process_meter(assignment, prev_billing_date, billing_date)
            if created:
                results['created'] += 1
        except Exception as e:
            logger.error(f'メーター処理エラー: {assignment.meter.meter_id} - {e}')
            results['errors'] += 1
    
    return results


def get_previous_billing_date(calendar):
    """前月の検針日を取得"""
    if calendar.month == 4:
        prev_month = 3
        prev_fiscal_year = calendar.fiscal_year - 1
    elif calendar.month == 1:
        prev_month = 12
        prev_fiscal_year = calendar.fiscal_year
    else:
        prev_month = calendar.month - 1
        prev_fiscal_year = calendar.fiscal_year
    
    return BillingCalendar.objects.filter(
        zone=calendar.zone,
        fiscal_year=prev_fiscal_year,
        base_billing_day=calendar.base_billing_day,
        month=prev_month
    ).first()


def process_meter(assignment, period_start, period_end):
    """メーター単位で処理"""
    meter = assignment.meter
    
    # 既存チェック
    if BillingSummary.objects.filter(
        meter=meter,
        period_start=period_start,
        period_end=period_end
    ).exists():
        logger.info(f'既存データあり: {meter.meter_id}')
        return False
    
    # 前回の請求データを取得（みなし累計値を引き継ぐため）
    prev_billing = BillingSummary.objects.filter(
        meter=meter,
        period_end=period_start
    ).order_by('-period_end').first()
    
    # 今回検針日の実測データ取得
    curr_reading = MeterReading.objects.filter(
        meter=meter,
        timestamp__date=period_end
    ).order_by('-timestamp').first()
    
    # 前回検針日の実測データ取得
    prev_reading = MeterReading.objects.filter(
        meter=meter,
        timestamp__date=period_start
    ).order_by('-timestamp').first()
    
    # 実測累計値（発電量と売電量）
    curr_import = Decimal(str(curr_reading.import_kwh)) if curr_reading and curr_reading.import_kwh else None
    curr_export = Decimal(str(curr_reading.route_b_export_kwh)) if curr_reading and curr_reading.route_b_export_kwh else None
    prev_import = Decimal(str(prev_reading.import_kwh)) if prev_reading and prev_reading.import_kwh else None
    prev_export = Decimal(str(prev_reading.route_b_export_kwh)) if prev_reading and prev_reading.route_b_export_kwh else None
    
    # パターン判定と計算
    result = calculate_billing(
        meter=meter,
        prev_billing=prev_billing,
        prev_import=prev_import,
        prev_export=prev_export,
        curr_import=curr_import,
        curr_export=curr_export,
        period_start=period_start,
        period_end=period_end
    )
    
    # 保存
    BillingSummary.objects.create(
        meter=meter,
        project_id=assignment.project_id,
        project_name=assignment.project_name,
        zone=assignment.zone,
        base_billing_day=assignment.base_billing_day,
        period_start=period_start,
        period_end=period_end,
        prev_actual_value=prev_import,
        curr_actual_value=curr_import,
        mid_actual_value=result['mid_actual_value'],
        mid_actual_date=result['mid_actual_date'],
        prev_used_value=result['prev_used_value'],
        curr_used_value=result['curr_used_value'],
        actual_kwh=result['actual_kwh'],
        deemed_kwh=result['deemed_kwh'],
        total_kwh=result['total_kwh'],
        deemed_method=result['deemed_method'],
        is_first_billing=result['is_first_billing'],
        note=result['note']
    )
    
    logger.info(f'請求集計作成: {meter.meter_id} {period_start}〜{period_end} total={result["total_kwh"]}kWh（自家消費量）')
    return True


def calculate_billing(meter, prev_billing, prev_import, prev_export, curr_import, curr_export, period_start, period_end):
    """
    パターン判定と計算
    
    重要: PPA課金対象 = 自家消費量 = 発電量(import) - 売電量(route_b_export)
    
    パターン:
    1. 前回あり、今回あり → 自家消費量 = (curr_import - prev_import) - (curr_export - prev_export)
    2. 前回なし（初回）、今回あり → 自家消費量 = curr_import - curr_export（0基準）
    3. 前回みなし値、今回あり → みなし継続で計算
    4. 前回あり、今回なし、期間中あり → 実測分 + 6kWh × 残日数
    5. 前回あり、今回なし、期間中なし → 180kWh/月
    6. 前回なし、今回なし → 180kWh/月
    """
    result = {
        'mid_actual_value': None,
        'mid_actual_date': None,
        'prev_used_value': Decimal('0'),
        'curr_used_value': Decimal('0'),
        'actual_kwh': Decimal('0'),
        'deemed_kwh': Decimal('0'),
        'total_kwh': Decimal('0'),
        'deemed_method': 'none',
        'is_first_billing': False,
        'note': ''
    }
    
    days_in_period = (period_end - period_start).days
    
    # 前回の計算用値を決定
    if prev_billing:
        prev_used_import = prev_billing.curr_used_value
        prev_used_export = getattr(prev_billing, 'curr_used_export', None) or Decimal('0')
        is_first = False
    elif prev_import is not None:
        prev_used_import = prev_import
        prev_used_export = prev_export or Decimal('0')
        is_first = False
    else:
        prev_used_import = Decimal('0')
        prev_used_export = Decimal('0')
        is_first = True
    
    result['is_first_billing'] = is_first
    result['prev_used_value'] = prev_used_import
    
    # 今回検針値がある場合
    if curr_import is not None:
        curr_used_export = curr_export or Decimal('0')
        
        # 発電量の増分
        generation_delta = curr_import - prev_used_import
        # 売電量の増分
        export_delta = curr_used_export - prev_used_export
        
        # 自家消費量 = 発電量増分 - 売電量増分
        self_consumption = generation_delta - export_delta
        self_consumption = max(self_consumption, Decimal('0'))
        
        result['curr_used_value'] = curr_import
        result['actual_kwh'] = self_consumption
        result['deemed_kwh'] = Decimal('0')
        result['total_kwh'] = self_consumption  # ★ 修正: 自家消費量が課金対象
        result['deemed_method'] = 'none'
        
        if is_first:
            result['note'] = '初回検針（前回値0基準）'
        elif prev_billing and prev_billing.deemed_method != 'none':
            result['note'] = f'前回みなし値({prev_used_import}kWh)からの差分'
        else:
            result['note'] = f'自家消費量: 発電{generation_delta}kWh - 売電{export_delta}kWh'
        
        return result
    
    # 今回検針値がない場合 → 期間中データを探す
    mid_reading = MeterReading.objects.filter(
        meter=meter,
        timestamp__date__gt=period_start,
        timestamp__date__lt=period_end
    ).order_by('-timestamp').first()
    
    if mid_reading:
        # パターン4: 期間中データあり
        mid_import = Decimal(str(mid_reading.import_kwh)) if mid_reading.import_kwh else Decimal('0')
        mid_export = Decimal(str(mid_reading.route_b_export_kwh)) if mid_reading.route_b_export_kwh else Decimal('0')
        mid_actual_date = mid_reading.timestamp.date()
        
        result['mid_actual_value'] = mid_import
        result['mid_actual_date'] = mid_actual_date
        
        # 実測分の自家消費量
        generation_delta = mid_import - prev_used_import
        export_delta = mid_export - prev_used_export
        actual_self_consumption = max(generation_delta - export_delta, Decimal('0'))
        
        # みなし分: 中間日から検針終了日までの日数 × 6kWh
        remaining_days = (period_end - mid_actual_date).days
        deemed_kwh = DEEMED_DAILY_KWH * remaining_days
        
        result['prev_used_value'] = prev_used_import
        result['curr_used_value'] = mid_import + deemed_kwh  # 計算用累計値
        result['actual_kwh'] = actual_self_consumption
        result['deemed_kwh'] = deemed_kwh
        result['total_kwh'] = actual_self_consumption + deemed_kwh  # ★ 自家消費量ベース
        result['deemed_method'] = 'daily'
        result['note'] = f'期間中最新データ({mid_actual_date})以降は6kWh/日×{remaining_days}日でみなし計算'
        
        return result
    
    # パターン5, 6: 期間中データなし → 180kWh/月固定
    result['deemed_kwh'] = DEEMED_MONTHLY_KWH
    result['actual_kwh'] = Decimal('0')
    result['total_kwh'] = DEEMED_MONTHLY_KWH  # みなし自家消費量
    result['curr_used_value'] = prev_used_import + DEEMED_MONTHLY_KWH
    result['deemed_method'] = 'monthly'
    
    if is_first:
        result['note'] = '初回検針かつデータ取得なし。180kWh/月でみなし計算'
    else:
        result['note'] = '今回検針データなし。180kWh/月でみなし計算'
    
    return result


@shared_task
def reset_stale_processing():
    """
    1時間以上processingのままのBillingSummaryをpendingに戻す
    毎時実行を想定
    """
    threshold = timezone.now() - timedelta(hours=1)
    
    count = BillingSummary.objects.filter(
        fetch_status='processing',
        fetch_started_at__lt=threshold
    ).update(
        fetch_status='pending',
        fetch_started_at=None
    )
    
    if count > 0:
        logger.warning(f"Reset {count} stale processing BillingSummaries to pending")
    
    return {'reset_count': count}