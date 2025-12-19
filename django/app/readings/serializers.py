from rest_framework import serializers
from .models import MeterReading, DailySummary, MonthlySummary


class MeterReadingSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeterReading
        fields = ['id', 'meter', 'recorded_at', 'received_at', 'import_kwh', 'export_kwh', 'pv_energy_kwh', 'pyranometer', 'created_at']


class DailySummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = DailySummary
        fields = ['id', 'meter', 'date', 'total_import_kwh', 'total_export_kwh', 'total_pv_kwh', 'record_count', 'calculated_at']


class MonthlySummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = MonthlySummary
        fields = ['id', 'meter', 'year_month', 'total_import_kwh', 'total_export_kwh', 'total_pv_kwh', 'calculated_at']