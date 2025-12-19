from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import Alert
from app.meters.models import Meter


@shared_task
def check_communication_alerts():
    threshold = timezone.now() - timedelta(hours=2)

    meters = Meter.objects.filter(
        is_deleted=False,
        status='active'
    ).exclude(
        last_received_at__gte=threshold
    )

    for meter in meters:
        existing = Alert.objects.filter(
            meter=meter,
            alert_type='communication',
            status__in=['open', 'acknowledged']
        ).exists()

        if not existing:
            Alert.objects.create(
                meter=meter,
                alert_type='communication',
                message=f'メーター {meter.meter_id} からの通信が途絶えています。最終受信: {meter.last_received_at}'
            )