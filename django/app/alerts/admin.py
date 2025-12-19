from django.contrib import admin
from .models import Alert


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ['meter', 'alert_type', 'status', 'detected_at', 'resolved_at']
    list_filter = ['alert_type', 'status']
    search_fields = ['meter__meter_id']