from django.contrib import admin
from .models import Meter, MeterAssignment


@admin.register(Meter)
class MeterAdmin(admin.ModelAdmin):
    list_display = ['meter_id', 'status', 'b_route_enabled', 'get_project_name', 'get_zone', 'installed_at', 'last_received_at', 'is_deleted']
    list_filter = ['status', 'b_route_enabled', 'is_deleted']
    search_fields = ['meter_id']
    ordering = ['-id']

    def get_project_name(self, obj):
        assignment = obj.current_assignment
        return assignment.project_name if assignment else '-'
    get_project_name.short_description = '案件名'

    def get_zone(self, obj):
        assignment = obj.current_assignment
        return assignment.zone_display if assignment else '-'
    get_zone.short_description = '電力管轄'


@admin.register(MeterAssignment)
class MeterAssignmentAdmin(admin.ModelAdmin):
    list_display = ['meter', 'project_id', 'project_name', 'zone', 'base_billing_day', 'start_date', 'end_date', 'synced_at']
    list_filter = ['zone', 'start_date', 'end_date']
    search_fields = ['meter__meter_id', 'project_name']
    ordering = ['-start_date']