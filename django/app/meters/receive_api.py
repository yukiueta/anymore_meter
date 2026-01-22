"""
メーターデータ受信API
Lambda から POST で呼び出される
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.conf import settings
from django.utils import timezone
import logging
import secrets

from app.meters.models import Meter
from app.readings.models import MeterReading, MeterEvent
from app.keys.models import MeterKey
from app.keys.crypto import decrypt_hex, try_decrypt, DEFAULT_KEY
from app.keys.protocol import (
    MessageParser, CMD_KEY_EXCHANGE, CMD_INTERVAL_DATA, CMD_EVENT_LOG
)
from app.keys.mqtt_service import (
    send_key_response_new, send_key_response_reconnect, send_key_confirm
)

logger = logging.getLogger(__name__)


def generate_key() -> str:
    """16文字のランダムキーを生成（ASCII印字可能文字）"""
    chars = ''.join(chr(i) for i in range(0x21, 0x7F))
    return ''.join(secrets.choice(chars) for _ in range(16))


class MeterReceiveView(APIView):
    """
    メーターデータ受信エンドポイント
    POST /api/meter/receive/
    
    Lambda から以下の形式で呼び出される:
    {
        "meter_id": "METER001",
        "topic": "METER001C2S",
        "payload": "HEX文字列（暗号化済み）",
        "timestamp": "2025-01-01T00:00:00Z"
    }
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        # Lambda認証（簡易）
        api_key = request.headers.get('X-API-Key', '')
        expected_key = getattr(settings, 'LAMBDA_API_KEY', '')
        if expected_key and api_key != expected_key:
            return Response({'error': 'unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)
        
        meter_id = request.data.get('meter_id', '')
        payload_hex = request.data.get('payload', '')
        
        if not meter_id or not payload_hex:
            return Response({'error': 'missing meter_id or payload'}, status=status.HTTP_400_BAD_REQUEST)
        
        logger.info(f'Received data from {meter_id}: {payload_hex[:50]}...')
        
        # メーター取得または作成
        meter, created = Meter.objects.get_or_create(
            meter_id=meter_id,
            defaults={'status': 'pending'}
        )
        
        if created:
            logger.info(f'New meter registered: {meter_id}')
        
        # 鍵取得
        try:
            meter_key = MeterKey.objects.get(meter=meter)
        except MeterKey.DoesNotExist:
            meter_key = None
        
        # 復号試行
        decrypted_hex = None
        used_key = None
        
        if meter_key:
            keys_to_try = [
                ('data_key', meter_key.data_key),
                ('master_key', meter_key.master_key),
                ('default_key', DEFAULT_KEY),
            ]
        else:
            keys_to_try = [
                ('default_key', DEFAULT_KEY),
            ]
        
        decrypted_hex, used_key = try_decrypt(payload_hex, keys_to_try)
        
        if not decrypted_hex:
            logger.error(f'Failed to decrypt data from {meter_id}')
            return Response({'error': 'decryption failed'}, status=status.HTTP_400_BAD_REQUEST)
        
        logger.debug(f'Decrypted with {used_key}: {decrypted_hex[:50]}...')
        
        # 電文パース
        try:
            parser = MessageParser(decrypted_hex)
            header = parser.parse_header()
            command_id = header['command_id']
        except Exception as e:
            logger.error(f'Failed to parse header: {e}')
            return Response({'error': 'parse error'}, status=status.HTTP_400_BAD_REQUEST)
        
        # コマンド別処理
        parser = MessageParser(decrypted_hex)  # リセット
        
        if command_id.endswith('0101B') or '0101B' in command_id:
            return self.handle_key_exchange(meter, meter_key, parser, used_key)
        elif command_id.endswith('00300B') or '00300B' in command_id:
            return self.handle_interval_data(meter, parser, decrypted_hex)
        elif command_id.endswith('00500B') or '00500B' in command_id:
            return self.handle_event_log(meter, parser, decrypted_hex)
        else:
            logger.warning(f'Unknown command: {command_id}')
            return Response({'status': 'unknown_command', 'command_id': command_id})
    
    def handle_key_exchange(self, meter, meter_key, parser, used_key):
        """鍵交換処理"""
        data = parser.parse_key_exchange()
        param = data['parameter']
        
        logger.info(f'Key exchange from {meter.meter_id}: type={data["type"]}, param={param}')
        
        if param == 0:
            # 新規登録（default keyで暗号化されている）
            if used_key != 'default_key':
                logger.warning(f'New registration but not using default key')
            
            # 鍵生成
            master_key = generate_key()
            data_key = generate_key()
            
            # 保存
            if meter_key:
                meter_key.master_key = master_key
                meter_key.data_key = data_key
                meter_key.key_version += 1
                meter_key.save()
            else:
                meter_key = MeterKey.objects.create(
                    meter=meter,
                    master_key=master_key,
                    data_key=data_key,
                )
            
            # 応答送信
            success = send_key_response_new(meter.meter_id, master_key, data_key)
            
            return Response({
                'status': 'key_exchange_initiated',
                'type': 'new_registration',
                'response_sent': success,
            })
        
        elif param == 1:
            # 再接続（master keyで暗号化されている）
            if not meter_key:
                logger.error(f'Reconnection but no key found for {meter.meter_id}')
                return Response({'error': 'no key found'}, status=status.HTTP_400_BAD_REQUEST)
            
            # 新しいdata key生成
            new_data_key = generate_key()
            old_data_key = meter_key.data_key
            
            meter_key.data_key = new_data_key
            meter_key.key_version += 1
            meter_key.last_key_exchange = timezone.now()
            meter_key.save()
            
            # 応答送信
            success = send_key_response_reconnect(
                meter.meter_id, new_data_key, meter_key.master_key
            )
            
            return Response({
                'status': 'key_exchange_initiated',
                'type': 'reconnection',
                'response_sent': success,
            })
        
        elif param == 2:
            # ACK
            if meter_key:
                if not meter_key.registered_at:
                    meter_key.registered_at = timezone.now()
                meter_key.last_key_exchange = timezone.now()
                meter_key.save()
            
            meter.status = 'active'
            meter.registered_at = meter.registered_at or timezone.now()
            meter.save()
            
            # 確認応答送信
            if meter_key:
                send_key_confirm(meter.meter_id, meter_key.data_key)
            
            return Response({
                'status': 'key_exchange_completed',
            })
        
        return Response({'status': 'unknown_key_exchange_type'})
    
    def handle_interval_data(self, meter, parser, raw_hex):
        """30分値データ処理"""
        data = parser.parse_interval_data()
        
        if not data['timestamp']:
            logger.error(f'Invalid timestamp in interval data')
            return Response({'error': 'invalid timestamp'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 保存
        reading, created = MeterReading.objects.update_or_create(
            meter=meter,
            timestamp=data['timestamp'],
            reading_type='interval',
            defaults={
                'import_kwh': data['import_kwh'],
                'export_kwh': data['export_kwh'],
                'route_b_import_kwh': data['route_b_import_kwh'],
                'route_b_export_kwh': data['route_b_export_kwh'],
                'raw_data': raw_hex,
            }
        )
        
        # メーター最終受信更新
        meter.last_received_at = timezone.now()
        if meter.status != 'active':
            meter.status = 'active'
        meter.save()
        
        logger.info(f'Saved interval data: {meter.meter_id} @ {data["timestamp"]}')
        
        return Response({
            'status': 'saved',
            'created': created,
            'timestamp': data['timestamp'].isoformat(),
            'import_kwh': str(data['import_kwh']),
            'route_b_export_kwh': str(data['route_b_export_kwh']),
        })
    
    def handle_event_log(self, meter, parser, raw_hex):
        """イベントログ処理"""
        data = parser.parse_event_log()
        
        event = MeterEvent.objects.create(
            meter=meter,
            timestamp=data['timestamp'] or timezone.now(),
            record_no=data['record_no'],
            event_code=data['event_code'],
            import_kwh=data['import_kwh'],
            raw_data=raw_hex,
        )
        
        logger.info(f'Saved event: {meter.meter_id} - {data["event_code"]}')
        
        return Response({
            'status': 'saved',
            'event_id': event.id,
            'event_code': data['event_code'],
        })