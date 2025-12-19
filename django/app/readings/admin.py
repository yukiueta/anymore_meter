from django.contrib import admin
from .models import MeterReading, DailySummary, MonthlySummary


@admin.register(MeterReading)
class MeterReadingAdmin(admin.ModelAdmin):
    list_display = ['meter', 'recorded_at', 'pv_energy_kwh', 'import_kwh', 'export_kwh']
    list_filter = ['meter', 'recorded_at']


@admin.register(DailySummary)
class DailySummaryAdmin(admin.ModelAdmin):
    list_display = ['meter', 'date', 'total_pv_kwh', 'record_count']
    list_filter = ['meter', 'date']


@admin.register(MonthlySummary)
class MonthlySummaryAdmin(admin.ModelAdmin):
    list_display = ['meter', 'year_month', 'total_pv_kwh']
    list_filter = ['meter', 'year_month']