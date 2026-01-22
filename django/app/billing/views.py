from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q, Sum, Count
from django.db.models.functions import Cast
from django.db.models import IntegerField
from django.http import HttpResponse
import csv
import io
from django.utils import timezone
from django.conf import settings
from datetime import datetime
from .models import BillingCalendar, BillingSummary
from .serializers import BillingCalendarSerializer, BillingSummarySerializer


class BillingCalendarListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        calendars = BillingCalendar.objects.all().annotate(
            base_day_int=Cast('base_billing_day', IntegerField())
        ).order_by('zone', 'fiscal_year', 'base_day_int', 'month')
        
        if request.GET.get('zone'):
            calendars = calendars.filter(zone=request.GET['zone'])
        if request.GET.get('fiscal_year'):
            calendars = calendars.filter(fiscal_year=request.GET['fiscal_year'])
        if request.GET.get('base_billing_day'):
            calendars = calendars.filter(base_billing_day=request.GET['base_billing_day'])
        
        return Response({
            'items': BillingCalendarSerializer(calendars, many=True).data,
            'total': calendars.count()
        })


class BillingCalendarImportView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    def post(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'ファイルが必要です'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            decoded = file.read().decode('utf-8-sig')
            reader = csv.DictReader(io.StringIO(decoded))
            
            records = []
            errors = []
            row_num = 1
            
            for row in reader:
                row_num += 1
                try:
                    zone = int(row['zone'])
                    fiscal_year = int(row['fiscal_year'])
                    base_billing_day = row['base_billing_day'].zfill(2)
                    month = int(row['month'])
                    actual_billing_date = datetime.strptime(row['actual_billing_date'], '%Y-%m-%d').date()
                    
                    if zone < 1 or zone > 10:
                        errors.append(f'行{row_num}: 電力管轄が不正です')
                        continue
                    if month < 1 or month > 12:
                        errors.append(f'行{row_num}: 月が不正です')
                        continue
                    
                    records.append(BillingCalendar(
                        zone=zone,
                        fiscal_year=fiscal_year,
                        base_billing_day=base_billing_day,
                        month=month,
                        actual_billing_date=actual_billing_date
                    ))
                except KeyError as e:
                    errors.append(f'行{row_num}: 必須列がありません - {e}')
                except ValueError as e:
                    errors.append(f'行{row_num}: 値が不正です - {e}')
            
            if errors:
                return Response({
                    'error': 'インポートエラー',
                    'details': errors[:20]
                }, status=status.HTTP_400_BAD_REQUEST)
            
            with transaction.atomic():
                if records:
                    zones = set(r.zone for r in records)
                    years = set(r.fiscal_year for r in records)
                    BillingCalendar.objects.filter(zone__in=zones, fiscal_year__in=years).delete()
                    BillingCalendar.objects.bulk_create(records)
            
            return Response({
                'message': f'{len(records)}件のデータをインポートしました',
                'count': len(records)
            })
        
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class BillingCalendarDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        zone = request.GET.get('zone')
        fiscal_year = request.GET.get('fiscal_year')
        
        if not zone or not fiscal_year:
            return Response({'error': '電力管轄と年度を指定してください'}, status=status.HTTP_400_BAD_REQUEST)
        
        deleted, _ = BillingCalendar.objects.filter(zone=zone, fiscal_year=fiscal_year).delete()
        
        return Response({
            'message': f'{deleted}件のデータを削除しました',
            'count': deleted
        })


class BillingCalendarExportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        calendars = BillingCalendar.objects.all().order_by('zone', 'fiscal_year', 'base_billing_day', 'month')
        
        if request.GET.get('zone'):
            calendars = calendars.filter(zone=request.GET['zone'])
        if request.GET.get('fiscal_year'):
            calendars = calendars.filter(fiscal_year=request.GET['fiscal_year'])
        
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = 'attachment; filename="billing_calendar.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['zone', 'fiscal_year', 'base_billing_day', 'month', 'actual_billing_date'])
        
        for c in calendars:
            writer.writerow([
                c.zone,
                c.fiscal_year,
                c.base_billing_day,
                c.month,
                c.actual_billing_date.strftime('%Y-%m-%d')
            ])
        
        return response


class BillingCalendarSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """登録済みの電力管轄・年度の一覧を取得"""
        summary = BillingCalendar.objects.values('zone', 'fiscal_year').annotate(
            count=Count('id'),
            base_days=Count('base_billing_day', distinct=True)
        ).order_by('zone', 'fiscal_year')
        
        zone_dict = dict(BillingCalendar.ZONE_CHOICES)
        result = []
        for item in summary:
            result.append({
                'zone': item['zone'],
                'zone_display': zone_dict.get(item['zone'], ''),
                'fiscal_year': item['fiscal_year'],
                'count': item['count'],
                'base_days': item['base_days']
            })
        
        return Response({'items': result})


class ZoneChoicesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        choices = [{'value': c[0], 'label': c[1]} for c in BillingCalendar.ZONE_CHOICES if c[0] != 0]
        return Response({'items': choices})


class BillingSummaryGroupListView(APIView):
    """請求集計：検針日×管轄のグループ一覧"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        year = request.GET.get('year')
        zone = request.GET.get('zone')

        queryset = BillingSummary.objects.values('zone', 'period_start', 'period_end').annotate(
            meter_count=Count('id'),
            total_actual=Sum('actual_kwh'),
            total_deemed=Sum('deemed_kwh'),
            total_kwh=Sum('total_kwh'),
            missing_count=Count('id', filter=~Q(deemed_method='none')),
            # 追加
            pending_count=Count('id', filter=Q(fetch_status='pending')),
            processing_count=Count('id', filter=Q(fetch_status='processing')),
            completed_count=Count('id', filter=Q(fetch_status='completed')),
            error_count=Count('id', filter=Q(fetch_status='error')),
        ).order_by('-period_end', 'zone')

        if year:
            queryset = queryset.filter(period_end__year=year)
        if zone:
            queryset = queryset.filter(zone=zone)

        # ページネーション
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 20))
        paginator = Paginator(list(queryset), per_page)
        page_obj = paginator.get_page(page)

        # zone_display追加
        zone_dict = dict(BillingCalendar.ZONE_CHOICES)
        items = []
        for item in page_obj:
            item['zone_display'] = zone_dict.get(item['zone'], '')
            items.append(item)

        return Response({
            'items': items,
            'total': paginator.count,
            'page': page,
            'per_page': per_page,
            'total_pages': paginator.num_pages
        })


class BillingSummaryDetailListView(APIView):
    """請求集計：メーター詳細一覧"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        zone = request.GET.get('zone')
        period_end = request.GET.get('period_end')
        search = request.GET.get('search', '').strip()

        if not zone or not period_end:
            return Response({'error': 'zone and period_end required'}, status=status.HTTP_400_BAD_REQUEST)

        queryset = BillingSummary.objects.filter(
            zone=zone,
            period_end=period_end
        ).select_related('meter').order_by('project_id')

        if search:
            queryset = queryset.filter(
                Q(meter__meter_id__icontains=search) |
                Q(project_name__icontains=search)
            )

        # ページネーション
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 20))
        paginator = Paginator(queryset, per_page)
        page_obj = paginator.get_page(page)

        serializer = BillingSummarySerializer(page_obj, many=True)

        # 集計
        totals = queryset.aggregate(
            total_actual=Sum('actual_kwh'),
            total_deemed=Sum('deemed_kwh'),
            total_kwh=Sum('total_kwh')
        )

        return Response({
            'items': serializer.data,
            'total': paginator.count,
            'page': page,
            'per_page': per_page,
            'total_pages': paginator.num_pages,
            'totals': {
                'actual_kwh': totals['total_actual'] or 0,
                'deemed_kwh': totals['total_deemed'] or 0,
                'total_kwh': totals['total_kwh'] or 0,
            }
        })


class BillingSummaryExportView(APIView):
    """CSVエクスポート"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        zone = request.GET.get('zone')
        period_end = request.GET.get('period_end')

        queryset = BillingSummary.objects.select_related('meter').order_by('-period_end', 'zone', 'project_id')

        if zone:
            queryset = queryset.filter(zone=zone)
        if period_end:
            queryset = queryset.filter(period_end=period_end)

        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = 'attachment; filename="billing_summary.csv"'

        writer = csv.writer(response)
        writer.writerow([
            '検針開始日', '検針終了日', '電力管轄', '案件ID', '案件名', 'メーターID',
            '前回実測値', '今回実測値', '計算用前回値', '計算用今回値',
            '実測分(kWh)', 'みなし分(kWh)', '合計(kWh)',
            'みなし方法', '初回', '備考'
        ])

        for s in queryset:
            writer.writerow([
                s.period_start,
                s.period_end,
                s.get_zone_display(),
                s.project_id,
                s.project_name,
                s.meter.meter_id,
                s.prev_actual_value or '',
                s.curr_actual_value or '',
                s.prev_used_value,
                s.curr_used_value,
                s.actual_kwh,
                s.deemed_kwh,
                s.total_kwh,
                s.get_deemed_method_display(),
                '○' if s.is_first_billing else '',
                s.note
            ])

        return response


class BillingSummaryMeterView(APIView):
    """メーター単位の請求データ一覧"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        meter_id = request.GET.get('meter_id')
        if not meter_id:
            return Response({'error': 'meter_id required'}, status=status.HTTP_400_BAD_REQUEST)

        queryset = BillingSummary.objects.filter(
            meter_id=meter_id
        ).order_by('-period_end')

        # ページネーション
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 20))
        paginator = Paginator(queryset, per_page)
        page_obj = paginator.get_page(page)

        serializer = BillingSummarySerializer(page_obj, many=True)

        return Response({
            'items': serializer.data,
            'total': paginator.count,
            'page': page,
            'per_page': per_page,
            'total_pages': paginator.num_pages
        })


class BillingSummaryByProjectView(APIView):
    """Anymore向けAPI: 案件単位の請求データ取得"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        project_id = request.GET.get('project_id')
        period_start = request.GET.get('period_start')
        period_end = request.GET.get('period_end')

        if not project_id:
            return Response({'error': 'project_id required'}, status=status.HTTP_400_BAD_REQUEST)

        queryset = BillingSummary.objects.filter(
            project_id=project_id
        ).select_related('meter').order_by('-period_end')

        if period_start:
            queryset = queryset.filter(period_start__gte=period_start)
        if period_end:
            queryset = queryset.filter(period_end__lte=period_end)

        # 最新1件 or 全件
        latest = queryset.first()
        if not latest:
            return Response({'error': 'データが見つかりません'}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'meter_id': latest.meter.meter_id,
            'project_id': latest.project_id,
            'project_name': latest.project_name,
            'period_start': latest.period_start,
            'period_end': latest.period_end,
            'prev_actual_value': latest.prev_actual_value,
            'curr_actual_value': latest.curr_actual_value,
            'prev_used_value': latest.prev_used_value,
            'curr_used_value': latest.curr_used_value,
            'actual_kwh': latest.actual_kwh,
            'deemed_kwh': latest.deemed_kwh,
            'total_kwh': latest.total_kwh,
            'deemed_method': latest.deemed_method,
            'is_first_billing': latest.is_first_billing,
            'note': latest.note
        })

class BillingSummaryChartView(APIView):
    """請求データグラフ用（直近12期間）"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        meter_id = request.GET.get('meter_id')
        limit = int(request.GET.get('limit', 12))

        if not meter_id:
            return Response({'error': 'meter_id required'}, status=status.HTTP_400_BAD_REQUEST)

        queryset = BillingSummary.objects.filter(
            meter_id=meter_id
        ).order_by('-period_end')[:limit]

        data = []
        for item in queryset:
            data.append({
                'period_start': item.period_start,
                'period_end': item.period_end,
                'actual_kwh': item.actual_kwh,
                'deemed_kwh': item.deemed_kwh,
                'total_kwh': item.total_kwh,
                'deemed_method': item.deemed_method,
            })

        # 古い順に並べ替え
        data.reverse()

        return Response({'items': data})


class AnymoreApiAuthMixin:
    def check_api_key(self, request):
        key = request.headers.get('X-API-Key')
        expected = settings.ANYMORE_API_KEY
        print(f"DEBUG: received key = '{key}', expected = '{expected}'")  # 追加
        return key and key == expected

class BillingSummaryPendingView(APIView, AnymoreApiAuthMixin):
    """未処理のBillingSummaryを取得し、processingにマークする"""
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        print("=" * 50)
        print("DEBUG: BillingSummaryPendingView called")
        
        if not self.check_api_key(request):
            print("DEBUG: API key check failed")
            return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)
        
        print("DEBUG: API key check passed")
        
        limit = int(request.GET.get('limit', 500))
        print(f"DEBUG: limit = {limit}")
        
        # まず全件数を確認
        total_count = BillingSummary.objects.count()
        print(f"DEBUG: Total BillingSummary count = {total_count}")
        
        pending_count = BillingSummary.objects.filter(fetch_status='pending').count()
        print(f"DEBUG: Pending count (all) = {pending_count}")
        
        pending_with_project = BillingSummary.objects.filter(
            fetch_status='pending',
            project_id__isnull=False
        ).count()
        print(f"DEBUG: Pending count (with project_id) = {pending_with_project}")
        
        # project_idがnullのpendingデータ
        pending_without_project = BillingSummary.objects.filter(
            fetch_status='pending',
            project_id__isnull=True
        ).count()
        print(f"DEBUG: Pending count (without project_id) = {pending_without_project}")
        
        # fetch_statusの分布
        from django.db.models import Count
        status_dist = BillingSummary.objects.values('fetch_status').annotate(count=Count('id'))
        print(f"DEBUG: fetch_status distribution = {list(status_dist)}")
        
        queryset = BillingSummary.objects.filter(
            fetch_status='pending',
            project_id__isnull=False
        ).select_related('meter').order_by('period_end')[:limit]
        
        items = []
        ids = []
        
        for item in queryset:
            print(f"DEBUG: Processing item id={item.id}, project_id={item.project_id}, meter={item.meter.meter_id}")
            items.append({
                'id': item.id,
                'meter_id': item.meter.meter_id,
                'project_id': item.project_id,
                'project_name': item.project_name,
                'zone': item.zone,
                'period_start': item.period_start.isoformat(),
                'period_end': item.period_end.isoformat(),
                'actual_kwh': str(item.actual_kwh),
                'deemed_kwh': str(item.deemed_kwh),
                'total_kwh': str(item.total_kwh),
                'deemed_method': item.deemed_method,
                'is_first_billing': item.is_first_billing,
            })
            ids.append(item.id)
        
        print(f"DEBUG: Found {len(items)} items to return")
        print(f"DEBUG: IDs = {ids}")
        
        if ids:
            updated = BillingSummary.objects.filter(id__in=ids).update(
                fetch_status='processing',
                fetch_started_at=timezone.now()
            )
            print(f"DEBUG: Updated {updated} items to 'processing'")
        
        print("=" * 50)
        
        return Response({
            'items': items,
            'count': len(items)
        })


class BillingSummaryMarkProcessedView(APIView, AnymoreApiAuthMixin):
    """処理結果を受け取り、completed/errorにマークする"""
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        print("=" * 50)
        print("DEBUG: BillingSummaryMarkProcessedView called")
        
        if not self.check_api_key(request):
            print("DEBUG: API key check failed")
            return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)
        
        print("DEBUG: API key check passed")
        print(f"DEBUG: request.data = {request.data}")
        
        completed_ids = request.data.get('completed_ids', [])
        error_items = request.data.get('error_items', [])
        
        print(f"DEBUG: completed_ids = {completed_ids}")
        print(f"DEBUG: error_items = {error_items}")
        
        now = timezone.now()
        
        if completed_ids:
            updated = BillingSummary.objects.filter(id__in=completed_ids).update(
                fetch_status='completed',
                fetch_completed_at=now,
                fetch_error_message=''
            )
            print(f"DEBUG: Marked {updated} items as 'completed'")
        
        for item in error_items:
            updated = BillingSummary.objects.filter(id=item['id']).update(
                fetch_status='error',
                fetch_completed_at=now,
                fetch_error_message=item.get('message', '')[:1000]
            )
            print(f"DEBUG: Marked item {item['id']} as 'error': {item.get('message', '')[:100]}")
        
        print("=" * 50)
        
        return Response({
            'completed_count': len(completed_ids),
            'error_count': len(error_items)
        })

class BillingSummaryErrorsView(APIView, AnymoreApiAuthMixin):
    """エラー状態のBillingSummaryを取得"""
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        if not self.check_api_key(request):
            return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)
        
        queryset = BillingSummary.objects.filter(
            fetch_status='error'
        ).select_related('meter').order_by('period_end')
        
        items = []
        for item in queryset:
            items.append({
                'id': item.id,
                'meter_id': item.meter.meter_id,
                'project_id': item.project_id,
                'project_name': item.project_name,
                'zone': item.zone,
                'period_start': item.period_start.isoformat(),
                'period_end': item.period_end.isoformat(),
                'actual_kwh': str(item.actual_kwh),
                'deemed_kwh': str(item.deemed_kwh),
                'total_kwh': str(item.total_kwh),
                'deemed_method': item.deemed_method,
                'is_first_billing': item.is_first_billing,
                'error_message': item.fetch_error_message,
            })
        
        return Response({
            'items': items,
            'count': len(items)
        })


class BillingSummaryRetryView(APIView, AnymoreApiAuthMixin):
    """エラー状態のBillingSummaryをpendingに戻す"""
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        if not self.check_api_key(request):
            return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)
        
        ids = request.data.get('ids', [])
        
        if not ids:
            count = BillingSummary.objects.filter(
                fetch_status='error'
            ).update(
                fetch_status='pending',
                fetch_started_at=None,
                fetch_completed_at=None,
                fetch_error_message=''
            )
        else:
            count = BillingSummary.objects.filter(
                id__in=ids,
                fetch_status='error'
            ).update(
                fetch_status='pending',
                fetch_started_at=None,
                fetch_completed_at=None,
                fetch_error_message=''
            )
        
        return Response({
            'retried_count': count
        })


class BillingSummaryPendingByMonthView(APIView, AnymoreApiAuthMixin):
    """指定月の未処理BillingSummaryを取得し、processingにマーク"""
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        if not self.check_api_key(request):
            return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)
        
        year = request.GET.get('year')
        month = request.GET.get('month')
        
        if not year or not month:
            return Response({'error': 'year and month required'}, status=status.HTTP_400_BAD_REQUEST)
        
        queryset = BillingSummary.objects.filter(
            fetch_status='pending',
            project_id__isnull=False,
            period_end__year=int(year),
            period_end__month=int(month)
        ).select_related('meter').order_by('project_id')
        
        items = []
        ids = []
        
        for item in queryset:
            items.append({
                'id': item.id,
                'meter_id': item.meter.meter_id,
                'project_id': item.project_id,
                'project_name': item.project_name,
                'zone': item.zone,
                'period_start': item.period_start.isoformat(),
                'period_end': item.period_end.isoformat(),
                'actual_kwh': str(item.actual_kwh),
                'deemed_kwh': str(item.deemed_kwh),
                'total_kwh': str(item.total_kwh),
                'deemed_method': item.deemed_method,
                'is_first_billing': item.is_first_billing,
            })
            ids.append(item.id)
        
        if ids:
            BillingSummary.objects.filter(id__in=ids).update(
                fetch_status='processing',
                fetch_started_at=timezone.now()
            )
        
        return Response({
            'items': items,
            'count': len(items),
            'year': year,
            'month': month
        })


class BillingSummaryMatrixView(APIView, AnymoreApiAuthMixin):
    """案件×月のマトリクスステータスを返す"""
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        if not self.check_api_key(request):
            return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)
        
        year = int(request.GET.get('year', datetime.now().year))
        
        from datetime import date
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)
        
        # project_idを持つBillingSummaryを取得
        summaries = BillingSummary.objects.filter(
            project_id__isnull=False,
            period_end__gte=start_date,
            period_end__lte=end_date,
        ).values(
            'project_id', 'project_name',
            'period_end',
            'fetch_status', 'fetch_error_message'
        )
        
        # マトリクスデータを構築
        matrix = {}
        for s in summaries:
            project_id = str(s['project_id'])
            if project_id not in matrix:
                matrix[project_id] = {
                    'project_name': s['project_name'],
                    'months': {}
                }
            
            period_end = s['period_end']
            month_key = f"{period_end.year}-{period_end.month:02d}"
            matrix[project_id]['months'][month_key] = {
                'status': s['fetch_status'],
                'error_message': s['fetch_error_message'] or ''
            }
        
        # 月ごとの集計
        month_stats = {}
        for s in summaries:
            period_end = s['period_end']
            month_key = f"{period_end.year}-{period_end.month:02d}"
            if month_key not in month_stats:
                month_stats[month_key] = {'pending': 0, 'processing': 0, 'completed': 0, 'error': 0, 'total': 0}
            month_stats[month_key][s['fetch_status']] += 1
            month_stats[month_key]['total'] += 1
        
        return Response({
            'matrix': matrix,
            'month_stats': month_stats
        })

class BillingSummaryAllByMonthView(APIView, AnymoreApiAuthMixin):
    """指定月の全BillingSummaryを取得（force再計算用）"""
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        if not self.check_api_key(request):
            return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)
        
        year = request.GET.get('year')
        month = request.GET.get('month')
        
        if not year or not month:
            return Response({'error': 'year and month required'}, status=status.HTTP_400_BAD_REQUEST)
        
        queryset = BillingSummary.objects.filter(
            project_id__isnull=False,
            period_end__year=int(year),
            period_end__month=int(month)
        ).select_related('meter').order_by('project_id')
        
        items = []
        ids = []
        
        for item in queryset:
            items.append({
                'id': item.id,
                'meter_id': item.meter.meter_id,
                'project_id': item.project_id,
                'project_name': item.project_name,
                'zone': item.zone,
                'period_start': item.period_start.isoformat(),
                'period_end': item.period_end.isoformat(),
                'actual_kwh': str(item.actual_kwh),
                'deemed_kwh': str(item.deemed_kwh),
                'total_kwh': str(item.total_kwh),
                'deemed_method': item.deemed_method,
                'is_first_billing': item.is_first_billing,
            })
            ids.append(item.id)
        
        # processingにマーク
        if ids:
            BillingSummary.objects.filter(id__in=ids).update(
                fetch_status='processing',
                fetch_started_at=timezone.now()
            )
        
        return Response({
            'items': items,
            'count': len(items),
            'year': year,
            'month': month
        })