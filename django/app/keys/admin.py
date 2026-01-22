from django.contrib import admin
from .models import MeterKey


@admin.register(MeterKey)
class MeterKeyAdmin(admin.ModelAdmin):
    list_display = ['meter', 'key_version', 'registered_at', 'last_key_exchange']
    list_filter = ['key_version']
    search_fields = ['meter__meter_id']
    ordering = ['-id']