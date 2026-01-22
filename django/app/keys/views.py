# django/app/keys/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
import secrets
from .models import MeterKey
from .serializers import MeterKeySerializer, MeterKeyDetailSerializer


DEFAULT_KEY = '69aF7&3KY0_kk89@'


class KeyListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        keys = MeterKey.objects.select_related('meter').order_by('-id')
        
        if request.GET.get('meter_id'):
            keys = keys.filter(meter__meter_id__icontains=request.GET['meter_id'])
        if request.GET.get('registered') == 'true':
            keys = keys.filter(registered_at__isnull=False)
        elif request.GET.get('registered') == 'false':
            keys = keys.filter(registered_at__isnull=True)
        
        return Response(MeterKeySerializer(keys, many=True).data)


class KeyDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            key = MeterKey.objects.get(pk=pk)
        except MeterKey.DoesNotExist:
            return Response({'error': 'not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(MeterKeySerializer(key).data)


class KeyRevealView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            key = MeterKey.objects.get(pk=pk)
        except MeterKey.DoesNotExist:
            return Response({'error': 'not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(MeterKeyDetailSerializer(key).data)


class KeyCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        key = MeterKey.objects.create(
            meter_id=request.data.get('meter_id'),
            master_key=request.data.get('master_key', DEFAULT_KEY),
            data_key=request.data.get('data_key', DEFAULT_KEY),
        )
        return Response(MeterKeySerializer(key).data, status=status.HTTP_201_CREATED)


class KeyRegenerateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            key = MeterKey.objects.get(pk=pk)
        except MeterKey.DoesNotExist:
            return Response({'error': 'not found'}, status=status.HTTP_404_NOT_FOUND)

        chars = ''.join(chr(i) for i in range(0x21, 0x7F))
        key.master_key = ''.join(secrets.choice(chars) for _ in range(16))
        key.data_key = ''.join(secrets.choice(chars) for _ in range(16))
        key.key_version += 1
        key.last_key_exchange = None
        key.save()
        return Response({'status': 'regenerated', 'key_version': key.key_version})


class KeyResetView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            key = MeterKey.objects.get(pk=pk)
        except MeterKey.DoesNotExist:
            return Response({'error': 'not found'}, status=status.HTTP_404_NOT_FOUND)

        key.master_key = DEFAULT_KEY
        key.data_key = DEFAULT_KEY
        key.key_version = 1
        key.registered_at = None
        key.last_key_exchange = None
        key.save()
        return Response({'status': 'reset'})


class KeyBulkImportView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from app.meters.models import Meter
        
        keys_data = request.data.get('keys', [])
        created = 0
        updated = 0
        errors = []

        for item in keys_data:
            try:
                meter = Meter.objects.get(meter_id=item.get('meter_id'))
                key, is_created = MeterKey.objects.update_or_create(
                    meter=meter,
                    defaults={
                        'master_key': item.get('master_key', DEFAULT_KEY),
                        'data_key': item.get('data_key', DEFAULT_KEY),
                    }
                )
                if is_created:
                    created += 1
                else:
                    updated += 1
            except Meter.DoesNotExist:
                errors.append({'meter_id': item.get('meter_id'), 'error': 'meter not found'})
            except Exception as e:
                errors.append({'meter_id': item.get('meter_id'), 'error': str(e)})

        return Response({'created': created, 'updated': updated, 'errors': errors})