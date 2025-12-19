from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .models import Meter, MeterAssignment
from .serializers import MeterSerializer, MeterAssignmentSerializer


class MeterListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        meters = Meter.objects.filter(is_deleted=False)
        serializer = MeterSerializer(meters, many=True)
        return Response(serializer.data)


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