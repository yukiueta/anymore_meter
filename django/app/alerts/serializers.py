from rest_framework import serializers
from .models import Alert


class AlertSerializer(serializers.ModelSerializer):
    meter_id = serializers.CharField(source='meter.meter_id', read_only=True)

    class Meta:
        model = Alert
        fields = ['id', 'meter', 'meter_id', 'alert_type', 'status', 'message', 'detected_at', 'resolved_at', 'created_at', 'updated_at']