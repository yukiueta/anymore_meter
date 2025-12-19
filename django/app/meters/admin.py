from django.contrib import admin
from .models import Meter, MeterAssignment


@admin.register(Meter)
class MeterAdmin(admin.ModelAdmin):
    list_display = ['meter_id', 'status', 'last_received_at', 'registered_at']
    list_filter = ['status']
    search_fields = ['meter_id']


@admin.register(MeterAssignment)
class MeterAssignmentAdmin(admin.ModelAdmin):
    list_display = ['meter', 'project_id', 'start_date', 'end_date']
    list_filter = ['start_date', 'end_date']