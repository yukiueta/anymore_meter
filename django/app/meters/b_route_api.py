# django/app/meters/b_route_api.py
"""
Bルート設定コマンド送信関連

b_route_enabled の意味:
- False: 未送信（DBの設定がメーターに反映されていない）
- True: 送信済み（DBの設定がメーターに反映済み）
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
import logging

from app.meters.models import Meter
from app.keys.models import MeterKey
from app.keys.mqtt_service import send_b_route_config

logger = logging.getLogger(__name__)


class MeterBRouteCommandView(APIView):
    """Bルート設定コマンドをメーターに送信"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        try:
            meter = Meter.objects.get(pk=pk, is_deleted=False)
        except Meter.DoesNotExist:
            return Response({'error': 'not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # 鍵取得
        try:
            meter_key = MeterKey.objects.get(meter=meter)
        except MeterKey.DoesNotExist:
            return Response({'error': 'no key registered'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not meter_key.registered_at:
            return Response({'error': 'key exchange not completed'}, status=status.HTTP_400_BAD_REQUEST)
        
        # DBの値を送信
        success = send_b_route_config(
            meter.meter_id,
            meter.b_route_id,
            meter.b_route_password,
            meter_key.data_key
        )
        
        if success:
            meter.b_route_enabled = True  # 送信済みフラグ
            meter.save()
            
            logger.info(f'B-route config sent to {meter.meter_id}')
            return Response({'status': 'sent'})
        else:
            return Response({'error': 'send failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def trigger_b_route_config_on_assign(meter, assignment):
    """
    案件紐付け時にBルート設定を送信
    MeterAssignment作成後に呼び出す
    """
    if not meter.b_route_id or not meter.b_route_password:
        logger.info(f'B-route not configured for {meter.meter_id}')
        return False
    
    try:
        meter_key = MeterKey.objects.get(meter=meter)
        if not meter_key.registered_at:
            logger.info(f'Key exchange not completed for {meter.meter_id}')
            return False
    except MeterKey.DoesNotExist:
        logger.info(f'No key for {meter.meter_id}')
        return False
    
    success = send_b_route_config(
        meter.meter_id,
        meter.b_route_id,
        meter.b_route_password,
        meter_key.data_key
    )
    
    if success:
        meter.b_route_enabled = True
        meter.save()
    
    logger.info(f'B-route config on assign: {meter.meter_id} -> {success}')
    return success