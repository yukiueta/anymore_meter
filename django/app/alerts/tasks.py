from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import Alert
from .slack import send_slack_alert
from app.meters.models import Meter


@shared_task
def check_communication_alerts():
    threshold = timezone.now() - timedelta(hours=2)

    offline_meters = Meter.objects.filter(
        is_deleted=False,
        status='active'
    ).exclude(
        last_received_at__gte=threshold
    )

    for meter in offline_meters:
        existing = Alert.objects.filter(
            meter=meter,
            alert_type='communication',
            status='open'
        ).exists()

        if not existing:
            message = f'メーター {meter.meter_id} からの通信が途絶えています。最終受信: {meter.last_received_at}'
            Alert.objects.create(
                meter=meter,
                alert_type='communication',
                message=message
            )
            send_slack_alert(meter.meter_id, 'communication', message)

    recovered_meters = Meter.objects.filter(
        is_deleted=False,
        status='active',
        last_received_at__gte=threshold
    )

    Alert.objects.filter(
        meter__in=recovered_meters,
        alert_type='communication',
        status='open'
    ).update(
        status='resolved',
        resolved_at=timezone.now()
    )