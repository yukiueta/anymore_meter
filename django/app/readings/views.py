from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import MeterReading, DailySummary, MonthlySummary
from .serializers import MeterReadingSerializer, DailySummarySerializer, MonthlySummarySerializer


class ReadingListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = MeterReading.objects.all()

        meter_id = request.query_params.get('meter_id')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if meter_id:
            queryset = queryset.filter(meter_id=meter_id)
        if start_date:
            queryset = queryset.filter(recorded_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(recorded_at__lte=end_date)

        queryset = queryset.order_by('-recorded_at')[:1000]
        serializer = MeterReadingSerializer(queryset, many=True)
        return Response(serializer.data)


class ReadingDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            reading = MeterReading.objects.get(pk=pk)
        except MeterReading.DoesNotExist:
            return Response({'error': 'not found'}, status=404)
        serializer = MeterReadingSerializer(reading)
        return Response(serializer.data)


class DailySummaryListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = DailySummary.objects.all()

        meter_id = request.query_params.get('meter_id')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if meter_id:
            queryset = queryset.filter(meter_id=meter_id)
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)

        queryset = queryset.order_by('-date')
        serializer = DailySummarySerializer(queryset, many=True)
        return Response(serializer.data)


class DailySummaryDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            summary = DailySummary.objects.get(pk=pk)
        except DailySummary.DoesNotExist:
            return Response({'error': 'not found'}, status=404)
        serializer = DailySummarySerializer(summary)
        return Response(serializer.data)


class MonthlySummaryListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = MonthlySummary.objects.all()

        meter_id = request.query_params.get('meter_id')
        year = request.query_params.get('year')

        if meter_id:
            queryset = queryset.filter(meter_id=meter_id)
        if year:
            queryset = queryset.filter(year_month__startswith=year)

        queryset = queryset.order_by('-year_month')
        serializer = MonthlySummarySerializer(queryset, many=True)
        return Response(serializer.data)


class MonthlySummaryDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            summary = MonthlySummary.objects.get(pk=pk)
        except MonthlySummary.DoesNotExist:
            return Response({'error': 'not found'}, status=404)
        serializer = MonthlySummarySerializer(summary)
        return Response(serializer.data)