from django.contrib import admin
from .models import MeterReading, MeterEvent, DailySummary, MonthlySummary


@admin.register(MeterReading)
class MeterReadingAdmin(admin.ModelAdmin):
    list_display = ['meter', 'timestamp', 'import_kwh', 'export_kwh', 'route_b_import_kwh', 'route_b_export_kwh']
    list_filter = ['meter', 'timestamp', 'reading_type']
    search_fields = ['meter__meter_id']
    ordering = ['-timestamp']


@admin.register(MeterEvent)
class MeterEventAdmin(admin.ModelAdmin):
    list_display = ['meter', 'timestamp', 'event_code', 'event_description', 'import_kwh']
    list_filter = ['event_code', 'timestamp']
    search_fields = ['meter__meter_id']
    ordering = ['-timestamp']


@admin.register(DailySummary)
class DailySummaryAdmin(admin.ModelAdmin):
    list_display = ['meter', 'date', 'generation_kwh', 'export_kwh', 'self_consumption_kwh', 'grid_import_kwh', 'record_count']
    list_filter = ['meter', 'date']
    search_fields = ['meter__meter_id']
    ordering = ['-date']


@admin.register(MonthlySummary)
class MonthlySummaryAdmin(admin.ModelAdmin):
    list_display = ['meter', 'year_month', 'generation_kwh', 'export_kwh', 'self_consumption_kwh', 'grid_import_kwh']
    list_filter = ['meter', 'year_month']
    search_fields = ['meter__meter_id']
    ordering = ['-year_month']