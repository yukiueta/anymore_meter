# django/app/meters/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse
from django.utils import timezone
import csv
from .models import Meter, MeterAssignment
from .serializers import MeterSerializer, MeterDetailSerializer, MeterAssignmentSerializer
from .services import SekouApiClient

class PaginationMixin:
    def paginate(self, queryset, request):
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 20))
        total = queryset.count()
        total_pages = (total + per_page - 1) // per_page
        start = (page - 1) * per_page
        end = start + per_page
        return {
            'items': queryset[start:end],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': total_pages
            }
        }


class MeterListView(APIView, PaginationMixin):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        meters = Meter.objects.filter(is_deleted=False).order_by('-id')
        
        if request.GET.get('status'):
            meters = meters.filter(status=request.GET['status'])
        if request.GET.get('search'):
            meters = meters.filter(meter_id__icontains=request.GET['search'])
        if request.GET.get('project_id'):
            meter_ids = MeterAssignment.objects.filter(
                project_id=request.GET['project_id'],
                end_date__isnull=True
            ).values_list('meter_id', flat=True)
            meters = meters.filter(id__in=meter_ids)
        
        # setup_statusフィルタ
        setup_status = request.GET.get('setup_status')
        if setup_status:
            if setup_status == 'unlinked':
                # 紐付けなし
                assigned_meter_ids = MeterAssignment.objects.filter(
                    end_date__isnull=True
                ).values_list('meter_id', flat=True)
                meters = meters.exclude(id__in=assigned_meter_ids)
            elif setup_status == 'zone_missing':
                # 紐付けあり、zone未設定
                meter_ids = MeterAssignment.objects.filter(
                    end_date__isnull=True,
                    zone__isnull=True
                ).values_list('meter_id', flat=True)
                meters = meters.filter(id__in=meter_ids)
            elif setup_status == 'billing_day_missing':
                # 紐付けあり、zone設定済み、base_billing_day未設定
                meter_ids = MeterAssignment.objects.filter(
                    end_date__isnull=True,
                    zone__isnull=False
                ).exclude(
                    base_billing_day__gt=''
                ).values_list('meter_id', flat=True)
                meters = meters.filter(id__in=meter_ids)
            elif setup_status == 'complete':
                # 全て設定済み
                meter_ids = MeterAssignment.objects.filter(
                    end_date__isnull=True,
                    zone__isnull=False,
                    base_billing_day__gt=''
                ).values_list('meter_id', flat=True)
                meters = meters.filter(id__in=meter_ids)
        
        result = self.paginate(meters, request)
        return Response({
            'items': MeterSerializer(result['items'], many=True).data,
            'pagination': result['pagination']
        })

class MeterCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        installed_at = request.data.get('installed_at')
        meter = Meter.objects.create(
            meter_id=request.data.get('meter_id'),
            status=request.data.get('status', 'inactive'),
            b_route_enabled=request.data.get('b_route_enabled', True),
            b_route_id=request.data.get('b_route_id', ''),
            b_route_password=request.data.get('b_route_password', ''),
            installed_at=installed_at if installed_at else None,
        )
        return Response(MeterDetailSerializer(meter).data, status=status.HTTP_201_CREATED)


class MeterDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            meter = Meter.objects.get(pk=pk, is_deleted=False)
        except Meter.DoesNotExist:
            return Response({'error': 'not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(MeterDetailSerializer(meter).data)


class MeterUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            meter = Meter.objects.get(pk=pk, is_deleted=False)
        except Meter.DoesNotExist:
            return Response({'error': 'not found'}, status=status.HTTP_404_NOT_FOUND)

        meter.meter_id = request.data.get('meter_id', meter.meter_id)
        meter.status = request.data.get('status', meter.status)
        meter.b_route_enabled = request.data.get('b_route_enabled', meter.b_route_enabled)
        meter.b_route_id = request.data.get('b_route_id', meter.b_route_id)
        meter.b_route_password = request.data.get('b_route_password', meter.b_route_password)
        
        installed_at = request.data.get('installed_at')
        if installed_at is not None:
            meter.installed_at = installed_at if installed_at else None
        
        meter.save()
        return Response(MeterDetailSerializer(meter).data)


class MeterDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            meter = Meter.objects.get(pk=pk, is_deleted=False)
        except Meter.DoesNotExist:
            return Response({'error': 'not found'}, status=status.HTTP_404_NOT_FOUND)
        meter.is_deleted = True
        meter.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeterBRouteUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            meter = Meter.objects.get(pk=pk, is_deleted=False)
        except Meter.DoesNotExist:
            return Response({'error': 'not found'}, status=status.HTTP_404_NOT_FOUND)

        meter.b_route_enabled = request.data.get('b_route_enabled', meter.b_route_enabled)
        meter.b_route_id = request.data.get('b_route_id', meter.b_route_id)
        meter.b_route_password = request.data.get('b_route_password', meter.b_route_password)
        meter.save()
        # TODO: メーターへS2Cコマンド送信
        return Response({'status': 'updated'})


class MeterSyncProjectView(APIView):
    """施工管理APIから案件情報を同期"""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            meter = Meter.objects.get(pk=pk, is_deleted=False)
        except Meter.DoesNotExist:
            return Response({'error': 'not found'}, status=status.HTTP_404_NOT_FOUND)

        assignment = meter.current_assignment
        if not assignment:
            return Response({'error': 'no active assignment'}, status=status.HTTP_400_BAD_REQUEST)

        # 施工管理APIから取得
        client = SekouApiClient()
        data, error = client.get_customer(assignment.project_id)
        
        if error:
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
        
        assignment.project_name = data.get('project_name', '')
        assignment.zone = data.get('zone') or None
        assignment.base_billing_day = data.get('base_billing_day', '')
        assignment.synced_at = timezone.now()
        assignment.save()

        return Response(MeterAssignmentSerializer(assignment).data)

class MeterAssignView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            meter = Meter.objects.get(pk=pk, is_deleted=False)
        except Meter.DoesNotExist:
            return Response({'error': 'not found'}, status=status.HTTP_404_NOT_FOUND)

        project_id = request.data.get('project_id')
        if not project_id:
            return Response({'error': 'project_id required'}, status=status.HTTP_400_BAD_REQUEST)
        
        start_date = request.data.get('start_date', timezone.now().date())

        # 既存の紐付けを終了
        MeterAssignment.objects.filter(
            meter=meter,
            end_date__isnull=True
        ).update(end_date=start_date)

        # 新規紐付け作成
        assignment = MeterAssignment.objects.create(
            meter=meter,
            project_id=project_id,
            project_name=request.data.get('project_name', ''),
            zone=request.data.get('zone'),
            base_billing_day=request.data.get('base_billing_day', ''),
            start_date=start_date
        )
        return Response(MeterAssignmentSerializer(assignment).data, status=status.HTTP_201_CREATED)

class MeterUnassignView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            meter = Meter.objects.get(pk=pk, is_deleted=False)
        except Meter.DoesNotExist:
            return Response({'error': 'not found'}, status=status.HTTP_404_NOT_FOUND)

        end_date = request.data.get('end_date', timezone.now().date())
        updated = MeterAssignment.objects.filter(
            meter=meter,
            end_date__isnull=True
        ).update(end_date=end_date)

        if updated:
            return Response({'status': 'unassigned'})
        return Response({'error': 'no active assignment'}, status=status.HTTP_400_BAD_REQUEST)


class MeterAssignmentUpdateView(APIView):
    """紐付けを編集"""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk, assignment_id):
        try:
            meter = Meter.objects.get(pk=pk, is_deleted=False)
        except Meter.DoesNotExist:
            return Response({'error': 'meter not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            assignment = MeterAssignment.objects.get(pk=assignment_id, meter=meter)
        except MeterAssignment.DoesNotExist:
            return Response({'error': 'assignment not found'}, status=status.HTTP_404_NOT_FOUND)

        assignment.project_id = request.data.get('project_id', assignment.project_id)
        assignment.project_name = request.data.get('project_name', assignment.project_name)
        assignment.zone = request.data.get('zone', assignment.zone)
        assignment.base_billing_day = request.data.get('base_billing_day', assignment.base_billing_day)
        assignment.start_date = request.data.get('start_date', assignment.start_date)
        if 'end_date' in request.data:
            assignment.end_date = request.data['end_date'] or None
        assignment.save()

        return Response(MeterAssignmentSerializer(assignment).data)


class MeterAssignmentDeleteView(APIView):
    """紐付けを削除"""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk, assignment_id):
        try:
            meter = Meter.objects.get(pk=pk, is_deleted=False)
        except Meter.DoesNotExist:
            return Response({'error': 'meter not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            assignment = MeterAssignment.objects.get(pk=assignment_id, meter=meter)
        except MeterAssignment.DoesNotExist:
            return Response({'error': 'assignment not found'}, status=status.HTTP_404_NOT_FOUND)

        assignment.delete()
        return Response({'status': 'deleted'})


class MeterBulkCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        meters_data = request.data.get('meters', [])
        created = 0
        errors = []

        for item in meters_data:
            try:
                Meter.objects.create(
                    meter_id=item.get('meter_id'),
                    status=item.get('status', 'inactive'),
                    b_route_enabled=item.get('b_route_enabled', True),
                    b_route_id=item.get('b_route_id', ''),
                    b_route_password=item.get('b_route_password', ''),
                    installed_at=item.get('installed_at'),
                )
                created += 1
            except Exception as e:
                errors.append({'meter_id': item.get('meter_id'), 'error': str(e)})

        return Response({'created': created, 'errors': errors})


class MeterExportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        meters = Meter.objects.filter(is_deleted=False).order_by('-id')
        
        if request.GET.get('status'):
            meters = meters.filter(status=request.GET['status'])
        if request.GET.get('search'):
            meters = meters.filter(meter_id__icontains=request.GET['search'])
        
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = f'attachment; filename="meters_{timezone.now().strftime("%Y%m%d")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'メーターID', 'ステータス', 'Bルート有効', 'BルートID',
            '設置日', '登録日', '最終受信日時', '紐付け案件ID'
        ])
        
        for m in meters:
            # 現在の紐付け案件取得
            assignment = MeterAssignment.objects.filter(
                meter=m, end_date__isnull=True
            ).first()
            project_id = assignment.project_id if assignment else ''
            
            writer.writerow([
                m.meter_id,
                m.status,
                '有効' if m.b_route_enabled else '無効',
                m.b_route_id or '',
                m.installed_at.strftime('%Y-%m-%d') if m.installed_at else '',
                m.registered_at.strftime('%Y-%m-%d %H:%M:%S') if m.registered_at else '',
                m.last_received_at.strftime('%Y-%m-%d %H:%M:%S') if m.last_received_at else '',
                project_id,
            ])
        
        return response

class SekouCustomerSearchView(APIView):
    """施工管理の案件を検索"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        search = request.GET.get('search', '')
        client = SekouApiClient()
        items, error = client.search_customers(search)
        
        if error:
            return Response({'error': error, 'items': []})
        
        return Response({'items': items})