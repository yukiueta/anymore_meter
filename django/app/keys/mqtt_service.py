"""
AWS IoT Core MQTT送信サービス
"""
import boto3
import json
import logging
from django.conf import settings
from .crypto import encrypt_hex, DEFAULT_KEY
from .protocol import (
    build_key_response_new,
    build_key_response_reconnect,
    build_key_confirm,
    build_b_route_config,
)

logger = logging.getLogger(__name__)

# IoT Core設定
IOT_ENDPOINT = getattr(settings, 'AWS_IOT_ENDPOINT', 'a3euups5uuz661-ats.iot.ap-northeast-1.amazonaws.com')
IOT_REGION = getattr(settings, 'AWS_IOT_REGION', 'ap-northeast-1')


def get_iot_client():
    """IoT Data Plane クライアント取得"""
    return boto3.client(
        'iot-data',
        region_name=IOT_REGION,
        endpoint_url=f'https://{IOT_ENDPOINT}'
    )


def publish_to_meter(meter_id: str, payload_hex: str, encrypt_key: str = None) -> bool:
    """
    メーターにMQTTメッセージを送信
    
    Args:
        meter_id: メーターID
        payload_hex: 送信データ（HEX文字列）
        encrypt_key: 暗号化キー（Noneの場合は平文）
    
    Returns:
        成功/失敗
    """
    topic = f'{meter_id}S2C'
    
    try:
        if encrypt_key:
            payload_hex = encrypt_hex(payload_hex, encrypt_key)
        
        client = get_iot_client()
        response = client.publish(
            topic=topic,
            qos=1,
            payload=bytes.fromhex(payload_hex)
        )
        
        logger.info(f'Published to {topic}: {payload_hex[:50]}...')
        return True
        
    except Exception as e:
        logger.error(f'Failed to publish to {topic}: {e}')
        return False


def send_key_response_new(meter_id: str, master_key: str, data_key: str) -> bool:
    """
    新規登録時の鍵交換応答を送信
    default keyで暗号化
    """
    payload = build_key_response_new(master_key, data_key)
    return publish_to_meter(meter_id, payload, DEFAULT_KEY)


def send_key_response_reconnect(meter_id: str, new_data_key: str, master_key: str) -> bool:
    """
    再接続時の鍵交換応答を送信
    master keyで暗号化
    """
    payload = build_key_response_reconnect(new_data_key)
    return publish_to_meter(meter_id, payload, master_key)


def send_key_confirm(meter_id: str, data_key: str) -> bool:
    """
    鍵交換完了確認を送信
    data keyで暗号化
    """
    payload = build_key_confirm()
    return publish_to_meter(meter_id, payload, data_key)


def send_b_route_config(meter_id: str, b_route_id: str, password: str, data_key: str) -> bool:
    """
    Bルート設定コマンドを送信
    
    Args:
        meter_id: メーターID
        b_route_id: BルートID（空文字で無効化）
        password: パスワード（空文字で無効化）
        data_key: 暗号化用データキー
    
    Returns:
        成功/失敗
    """
    payload = build_b_route_config(b_route_id, password)
    return publish_to_meter(meter_id, payload, data_key)


def send_b_route_disable(meter_id: str, data_key: str) -> bool:
    """Bルート無効化コマンドを送信"""
    return send_b_route_config(meter_id, '', '', data_key)