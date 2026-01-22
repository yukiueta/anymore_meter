from rest_framework import serializers
from .models import MeterReading, MeterEvent, DailySummary, MonthlySummary


class MeterReadingSerializer(serializers.ModelSerializer):
    meter_id = serializers.CharField(source='meter.meter_id', read_only=True)

    class Meta:
        model = MeterReading
        fields = [
            'id', 'meter', 'meter_id', 'timestamp', 'reading_type',
            'import_kwh', 'export_kwh',
            'route_b_import_kwh', 'route_b_export_kwh',
            'received_at', 'created_at'
        ]


class MeterEventSerializer(serializers.ModelSerializer):
    meter_id = serializers.CharField(source='meter.meter_id', read_only=True)

    class Meta:
        model = MeterEvent
        fields = [
            'id', 'meter', 'meter_id', 'timestamp', 'record_no',
            'event_code', 'event_description', 'import_kwh',
            'received_at', 'created_at'
        ]


class DailySummarySerializer(serializers.ModelSerializer):
    meter_id = serializers.CharField(source='meter.meter_id', read_only=True)

    class Meta:
        model = DailySummary
        fields = [
            'id', 'meter', 'meter_id', 'date',
            'generation_kwh', 'export_kwh', 'self_consumption_kwh',
            'grid_import_kwh',
            'record_count', 'calculated_at'
        ]


class MonthlySummarySerializer(serializers.ModelSerializer):
    meter_id = serializers.CharField(source='meter.meter_id', read_only=True)

    class Meta:
        model = MonthlySummary
        fields = [
            'id', 'meter', 'meter_id', 'year_month',
            'generation_kwh', 'export_kwh', 'self_consumption_kwh',
            'grid_import_kwh',
            'calculated_at'
        ]