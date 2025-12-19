from rest_framework import serializers
from .models import MeterKey


class MeterKeySerializer(serializers.ModelSerializer):
    meter_id = serializers.CharField(source='meter.meter_id', read_only=True)

    class Meta:
        model = MeterKey
        fields = ['id', 'meter', 'meter_id', 'master_key', 'data_key', 'created_at', 'updated_at']
        extra_kwargs = {
            'master_key': {'write_only': True},
            'data_key': {'write_only': True},
        }


class MeterKeyDetailSerializer(serializers.ModelSerializer):
    meter_id = serializers.CharField(source='meter.meter_id', read_only=True)

    class Meta:
        model = MeterKey
        fields = ['id', 'meter', 'meter_id', 'master_key', 'data_key', 'created_at', 'updated_at']