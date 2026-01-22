from rest_framework import serializers
from .models import BillingCalendar, BillingSummary


class BillingCalendarSerializer(serializers.ModelSerializer):
    zone_display = serializers.CharField(source='get_zone_display', read_only=True)

    class Meta:
        model = BillingCalendar
        fields = [
            'id', 'zone', 'zone_display', 'fiscal_year',
            'base_billing_day', 'month', 'actual_billing_date',
            'created_at', 'updated_at'
        ]


class BillingCalendarImportSerializer(serializers.Serializer):
    file = serializers.FileField()


class BillingSummarySerializer(serializers.ModelSerializer):
    meter_id = serializers.CharField(source='meter.meter_id', read_only=True)
    zone_display = serializers.CharField(source='get_zone_display', read_only=True)
    deemed_method_display = serializers.CharField(source='get_deemed_method_display', read_only=True)
    fetch_status_display = serializers.CharField(source='get_fetch_status_display', read_only=True)  # 追加

    class Meta:
        model = BillingSummary
        fields = [
            'id', 'meter', 'meter_id', 'project_id', 'project_name',
            'zone', 'zone_display', 'base_billing_day',
            'period_start', 'period_end',
            'prev_actual_value', 'curr_actual_value',
            'mid_actual_value', 'mid_actual_date',
            'prev_used_value', 'curr_used_value',
            'actual_kwh', 'deemed_kwh', 'total_kwh',
            'deemed_method', 'deemed_method_display',
            'is_first_billing', 'note',
            'fetch_status', 'fetch_status_display',  # 追加
            'fetch_error_message',  # 追加
            'created_at', 'updated_at'
        ]