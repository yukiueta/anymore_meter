from rest_framework import serializers
from .models import MeterKey


class MeterKeySerializer(serializers.ModelSerializer):
    meter_id = serializers.CharField(source='meter.meter_id', read_only=True)

    class Meta:
        model = MeterKey
        fields = [
            'id', 'meter', 'meter_id', 'key_version',
            'registered_at', 'last_key_exchange',
            'created_at', 'updated_at'
        ]


class MeterKeyDetailSerializer(serializers.ModelSerializer):
    meter_id = serializers.CharField(source='meter.meter_id', read_only=True)

    class Meta:
        model = MeterKey
        fields = [
            'id', 'meter', 'meter_id',
            'master_key', 'data_key', 'key_version',
            'registered_at', 'last_key_exchange',
            'created_at', 'updated_at'
        ]