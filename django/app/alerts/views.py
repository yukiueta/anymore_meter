from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .models import Alert
from .serializers import AlertSerializer


class AlertListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = Alert.objects.all()

        meter_id = request.query_params.get('meter_id')
        alert_type = request.query_params.get('type')
        alert_status = request.query_params.get('status')

        if meter_id:
            queryset = queryset.filter(meter_id=meter_id)
        if alert_type:
            queryset = queryset.filter(alert_type=alert_type)
        if alert_status:
            queryset = queryset.filter(status=alert_status)

        queryset = queryset.order_by('-detected_at')
        serializer = AlertSerializer(queryset, many=True)
        return Response(serializer.data)


class AlertDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            alert = Alert.objects.get(pk=pk)
        except Alert.DoesNotExist:
            return Response({'error': 'not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = AlertSerializer(alert)
        return Response(serializer.data)


class AlertAcknowledgeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            alert = Alert.objects.get(pk=pk)
        except Alert.DoesNotExist:
            return Response({'error': 'not found'}, status=status.HTTP_404_NOT_FOUND)

        alert.status = 'acknowledged'
        alert.save()
        serializer = AlertSerializer(alert)
        return Response(serializer.data)


class AlertResolveView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            alert = Alert.objects.get(pk=pk)
        except Alert.DoesNotExist:
            return Response({'error': 'not found'}, status=status.HTTP_404_NOT_FOUND)

        alert.status = 'resolved'
        alert.resolved_at = timezone.now()
        alert.save()
        serializer = AlertSerializer(alert)
        return Response(serializer.data)