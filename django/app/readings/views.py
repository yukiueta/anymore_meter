# django/app/readings/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse
from django.utils import timezone
from datetime import timedelta
import csv
from .models import MeterReading, MeterEvent, DailySummary, MonthlySummary
from .serializers import (
    MeterReadingSerializer, MeterEventSerializer,
    DailySummarySerializer, MonthlySummarySerializer
)


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


class ReadingListView(APIView, PaginationMixin):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        readings = MeterReading.objects.select_related('meter').order_by('-timestamp')
        
        if request.GET.get('meter_id'):
            readings = readings.filter(meter_id=request.GET['meter_id'])
        if request.GET.get('start_date'):
            readings = readings.filter(timestamp__date__gte=request.GET['start_date'])
        if request.GET.get('end_date'):
            readings = readings.filter(timestamp__date__lte=request.GET['end_date'])
        if request.GET.get('reading_type'):
            readings = readings.filter(reading_type=request.GET['reading_type'])
        
        result = self.paginate(readings, request)
        return Response({
            'items': MeterReadingSerializer(result['items'], many=True).data,
            'pagination': result['pagination']
        })


class ReadingDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            reading = MeterReading.objects.get(pk=pk)
        except MeterReading.DoesNotExist:
            return Response({'error': 'not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(MeterReadingSerializer(reading).data)


class ReadingExportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        readings = MeterReading.objects.select_related('meter').order_by('-timestamp')
        
        if request.GET.get('meter_id'):
            readings = readings.filter(meter_id=request.GET['meter_id'])
        if request.GET.get('start_date'):
            readings = readings.filter(timestamp__date__gte=request.GET['start_date'])
        if request.GET.get('end_date'):
            readings = readings.filter(timestamp__date__lte=request.GET['end_date'])
        
        readings = readings[:10000]
        
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = f'attachment; filename="readings_{timezone.now().strftime("%Y%m%d")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['メーターID', '計測日時', '種別', '発電量(kWh)', '逆潮流(kWh)', '買電(kWh)', '売電(kWh)', '受信日時'])
        
        for r in readings:
            writer.writerow([
                r.meter.meter_id,
                r.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                r.reading_type,
                r.import_kwh or '',
                r.export_kwh or '',
                r.route_b_import_kwh or '',
                r.route_b_export_kwh or '',
                r.received_at.strftime('%Y-%m-%d %H:%M:%S'),
            ])
        
        return response


class EventListView(APIView, PaginationMixin):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        events = MeterEvent.objects.select_related('meter').order_by('-timestamp')
        
        if request.GET.get('meter_id'):
            events = events.filter(meter_id=request.GET['meter_id'])
        if request.GET.get('event_code'):
            events = events.filter(event_code=request.GET['event_code'])
        if request.GET.get('start_date'):
            events = events.filter(timestamp__date__gte=request.GET['start_date'])
        if request.GET.get('end_date'):
            events = events.filter(timestamp__date__lte=request.GET['end_date'])
        
        result = self.paginate(events, request)
        return Response({
            'items': MeterEventSerializer(result['items'], many=True).data,
            'pagination': result['pagination']
        })


class EventDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            event = MeterEvent.objects.get(pk=pk)
        except MeterEvent.DoesNotExist:
            return Response({'error': 'not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(MeterEventSerializer(event).data)


class DailySummaryListView(APIView, PaginationMixin):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        summaries = DailySummary.objects.select_related('meter').order_by('-date')
        
        if request.GET.get('meter_id'):
            summaries = summaries.filter(meter_id=request.GET['meter_id'])
        if request.GET.get('start_date'):
            summaries = summaries.filter(date__gte=request.GET['start_date'])
        if request.GET.get('end_date'):
            summaries = summaries.filter(date__lte=request.GET['end_date'])
        
        result = self.paginate(summaries, request)
        return Response({
            'items': DailySummarySerializer(result['items'], many=True).data,
            'pagination': result['pagination']
        })


class DailySummaryDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            summary = DailySummary.objects.get(pk=pk)
        except DailySummary.DoesNotExist:
            return Response({'error': 'not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(DailySummarySerializer(summary).data)


class DailySummaryExportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        summaries = DailySummary.objects.select_related('meter').order_by('-date')
        
        if request.GET.get('meter_id'):
            summaries = summaries.filter(meter_id=request.GET['meter_id'])
        if request.GET.get('start_date'):
            summaries = summaries.filter(date__gte=request.GET['start_date'])
        if request.GET.get('end_date'):
            summaries = summaries.filter(date__lte=request.GET['end_date'])
        
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = f'attachment; filename="daily_{timezone.now().strftime("%Y%m%d")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['メーターID', '日付', '発電量(kWh)', '売電量(kWh)', '自家消費量(kWh)', '買電量(kWh)', 'レコード数'])
        
        for s in summaries:
            writer.writerow([
                s.meter.meter_id, s.date.strftime('%Y-%m-%d'),
                s.generation_kwh or '', s.export_kwh or '', s.self_consumption_kwh or '',
                s.grid_import_kwh or '', s.record_count
            ])
        
        return response


class MonthlySummaryListView(APIView, PaginationMixin):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        summaries = MonthlySummary.objects.select_related('meter').order_by('-year_month')
        
        if request.GET.get('meter_id'):
            summaries = summaries.filter(meter_id=request.GET['meter_id'])
        if request.GET.get('year'):
            summaries = summaries.filter(year_month__startswith=request.GET['year'])
        
        result = self.paginate(summaries, request)
        return Response({
            'items': MonthlySummarySerializer(result['items'], many=True).data,
            'pagination': result['pagination']
        })


class MonthlySummaryDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            summary = MonthlySummary.objects.get(pk=pk)
        except MonthlySummary.DoesNotExist:
            return Response({'error': 'not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(MonthlySummarySerializer(summary).data)


class MonthlySummaryExportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        summaries = MonthlySummary.objects.select_related('meter').order_by('-year_month')
        
        if request.GET.get('meter_id'):
            summaries = summaries.filter(meter_id=request.GET['meter_id'])
        if request.GET.get('year'):
            summaries = summaries.filter(year_month__startswith=request.GET['year'])
        
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = f'attachment; filename="monthly_{timezone.now().strftime("%Y%m%d")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['メーターID', '年月', '発電量(kWh)', '売電量(kWh)', '自家消費量(kWh)', '買電量(kWh)'])
        
        for s in summaries:
            writer.writerow([
                s.meter.meter_id, s.year_month,
                s.generation_kwh or '', s.export_kwh or '', s.self_consumption_kwh or '',
                s.grid_import_kwh or ''
            ])
        
        return response


class DailySummaryChartView(APIView):
    """日次集計グラフ用（直近N日）"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        meter_id = request.GET.get('meter_id')
        days = int(request.GET.get('days', 30))

        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)

        queryset = DailySummary.objects.filter(
            date__gte=start_date,
            date__lte=end_date
        ).order_by('date')

        if meter_id:
            queryset = queryset.filter(meter_id=meter_id)
        else:
            # メーター指定なしの場合は日別に集計
            from django.db.models import Sum
            queryset = DailySummary.objects.filter(
                date__gte=start_date,
                date__lte=end_date
            ).values('date').annotate(
                generation_kwh=Sum('generation_kwh'),
                export_kwh=Sum('export_kwh'),
                self_consumption_kwh=Sum('self_consumption_kwh'),
                grid_import_kwh=Sum('grid_import_kwh')
            ).order_by('date')

            data = list(queryset)
            return Response({'items': data})

        data = list(queryset.values(
            'date', 'generation_kwh', 'export_kwh',
            'self_consumption_kwh', 'grid_import_kwh'
        ))

        return Response({'items': data})


class MonthlySummaryChartView(APIView):
    """月次集計グラフ用（直近N月）"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        meter_id = request.GET.get('meter_id')
        months = int(request.GET.get('months', 12))

        if meter_id:
            queryset = MonthlySummary.objects.filter(
                meter_id=meter_id
            ).order_by('-year_month')[:months]

            data = list(queryset.values(
                'year_month', 'generation_kwh', 'export_kwh',
                'self_consumption_kwh', 'grid_import_kwh'
            ))
        else:
            # メーター指定なしの場合は月別に集計
            from django.db.models import Sum
            queryset = MonthlySummary.objects.values('year_month').annotate(
                generation_kwh=Sum('generation_kwh'),
                export_kwh=Sum('export_kwh'),
                self_consumption_kwh=Sum('self_consumption_kwh'),
                grid_import_kwh=Sum('grid_import_kwh')
            ).order_by('-year_month')[:months]

            data = list(queryset)

        # 古い順に並べ替え
        data.reverse()

        return Response({'items': data})