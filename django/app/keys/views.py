from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
import secrets
from .models import MeterKey
from .serializers import MeterKeySerializer, MeterKeyDetailSerializer


class KeyListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        keys = MeterKey.objects.all()
        serializer = MeterKeySerializer(keys, many=True)
        return Response(serializer.data)


class KeyCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        key = MeterKey.objects.create(
            meter_id=request.data.get('meter_id'),
            master_key=request.data.get('master_key'),
            data_key=request.data.get('data_key'),
        )
        serializer = MeterKeySerializer(key)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class KeyDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            key = MeterKey.objects.get(pk=pk)
        except MeterKey.DoesNotExist:
            return Response({'error': 'not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = MeterKeySerializer(key)
        return Response(serializer.data)


class KeyUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            key = MeterKey.objects.get(pk=pk)
        except MeterKey.DoesNotExist:
            return Response({'error': 'not found'}, status=status.HTTP_404_NOT_FOUND)

        key.master_key = request.data.get('master_key', key.master_key)
        key.data_key = request.data.get('data_key', key.data_key)
        key.save()
        serializer = MeterKeySerializer(key)
        return Response(serializer.data)


class KeyRevealView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            key = MeterKey.objects.get(pk=pk)
        except MeterKey.DoesNotExist:
            return Response({'error': 'not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = MeterKeyDetailSerializer(key)
        return Response(serializer.data)


class KeyRegenerateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            key = MeterKey.objects.get(pk=pk)
        except MeterKey.DoesNotExist:
            return Response({'error': 'not found'}, status=status.HTTP_404_NOT_FOUND)

        key.master_key = secrets.token_hex(8)
        key.data_key = secrets.token_hex(8)
        key.save()
        return Response({'status': 'regenerated'})


class KeyBulkImportView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        keys_data = request.data.get('keys', [])
        created = 0
        errors = []

        for item in keys_data:
            try:
                MeterKey.objects.update_or_create(
                    meter_id=item['meter_id'],
                    defaults={
                        'master_key': item['master_key'],
                        'data_key': item['data_key'],
                    }
                )
                created += 1
            except Exception as e:
                errors.append({'meter_id': item.get('meter_id'), 'error': str(e)})

        return Response({
            'created': created,
            'errors': errors
        })