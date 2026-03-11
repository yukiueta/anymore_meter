import requests
import logging
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


def send_slack_alert(meter_id: str, alert_type: str, message: str):
    webhook_url = getattr(settings, 'SLACK_WEBHOOK_URL', '')
    if not webhook_url:
        logger.warning('SLACK_WEBHOOK_URL が設定されていません')
        return

    type_labels = {
        'communication': '通信途絶',
        'anomaly': '異常値',
    }
    type_label = type_labels.get(alert_type, alert_type)

    payload = {
        'text': f':warning: *アラート発生: {type_label}*\n'
                f'*メーターID:* {meter_id}\n'
                f'*メッセージ:* {message}\n'
                f'*検知日時:* {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}'
    }

    try:
        response = requests.post(webhook_url, json=payload, timeout=5)
        response.raise_for_status()
    except Exception as e:
        logger.error(f'Slack通知失敗: {e}')