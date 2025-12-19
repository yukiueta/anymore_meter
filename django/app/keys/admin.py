from django.contrib import admin
from .models import MeterKey


@admin.register(MeterKey)
class MeterKeyAdmin(admin.ModelAdmin):
    list_display = ['meter', 'created_at', 'updated_at']
    search_fields = ['meter__meter_id']