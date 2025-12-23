from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .models import Meter, MeterAssignment
from .serializers import MeterSerializer, MeterAssignmentSerializer


class PaginationMixin:
    def paginate(self, queryset, request):
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 20))
        
        total = queryset.count()
        total_pages = (total + per_page - 1) // per_page
        
        start = (page - 1) * per_page
        end = start + per_page
        items = queryset[start:end]
        
        return {
            'items': items,
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
        result = self.paginate(meters, request)
        serializer = MeterSerializer(result['items'], many=True)
        return Response({
            'items': serializer.data,
            'pagination': result['pagination']
        })

class MeterCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        meter = Meter.objects.create(
            meter_id=request.data.get('meter_id'),
            status=request.data.get('status', 'registered'),
        )
        serializer = MeterSerializer(meter)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MeterDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            meter = Meter.objects.get(pk=pk, is_deleted=False)
        except Meter.DoesNotExist:
            return Response({'error': 'not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = MeterSerializer(meter)
        return Response(serializer.data)


class MeterUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            meter = Meter.objects.get(pk=pk, is_deleted=False)
        except Meter.DoesNotExist:
            return Response({'error': 'not found'}, status=status.HTTP_404_NOT_FOUND)

        meter.meter_id = request.data.get('meter_id', meter.meter_id)
        meter.status = request.data.get('status', meter.status)
        meter.save()
        serializer = MeterSerializer(meter)
        return Response(serializer.data)

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


class MeterAssignProjectView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            meter = Meter.objects.get(pk=pk, is_deleted=False)
        except Meter.DoesNotExist:
            return Response({'error': 'not found'}, status=status.HTTP_404_NOT_FOUND)

        project_id = request.data.get('project_id')
        start_date = request.data.get('start_date', timezone.now().date())

        MeterAssignment.objects.filter(
            meter=meter,
            end_date__isnull=True
        ).update(end_date=start_date)

        assignment = MeterAssignment.objects.create(
            meter=meter,
            project_id=project_id,
            start_date=start_date
        )

        serializer = MeterAssignmentSerializer(assignment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MeterUnassignProjectView(APIView):
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
        return Response({'status': 'no active assignment'}, status=status.HTTP_400_BAD_REQUEST)

class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from app.readings.models import MeterReading
        from app.alerts.models import Alert
        from django.utils import timezone
        from datetime import timedelta

        today = timezone.now().date()
        
        meter_count = Meter.objects.filter(is_deleted=False, status='active').count()
        today_readings = MeterReading.objects.filter(
            recorded_at__date=today
        ).count()
        open_alerts = Alert.objects.filter(status='open').count()

        return Response({
            'meter_count': meter_count,
            'today_readings': today_readings,
            'open_alerts': open_alerts
        })