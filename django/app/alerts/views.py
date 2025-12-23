from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .models import Alert
from .serializers import AlertSerializer


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


class AlertListView(APIView, PaginationMixin):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        alerts = Alert.objects.all().order_by('-detected_at')
        
        status_filter = request.GET.get('status')
        type_filter = request.GET.get('type')
        
        if status_filter:
            alerts = alerts.filter(status=status_filter)
        if type_filter:
            alerts = alerts.filter(alert_type=type_filter)
        
        result = self.paginate(alerts, request)
        serializer = AlertSerializer(result['items'], many=True)
        return Response({
            'items': serializer.data,
            'pagination': result['pagination']
        })


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
        return Response({'status': 'acknowledged'})


class AlertResolveView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            alert = Alert.objects.get(pk=pk)
        except Alert.DoesNotExist:
            return Response({'error': 'not found'}, status=status.HTTP_404_NOT_FOUND)
        
        alert.status = 'resolved'
        alert.save()
        return Response({'status': 'resolved'})

