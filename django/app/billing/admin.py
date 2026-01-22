from django.contrib import admin
from .models import BillingCalendar, BillingSummary


@admin.register(BillingCalendar)
class BillingCalendarAdmin(admin.ModelAdmin):
    list_display = ['zone', 'fiscal_year', 'base_billing_day', 'month', 'actual_billing_date']
    list_filter = ['zone', 'fiscal_year', 'base_billing_day']
    search_fields = ['base_billing_day']
    ordering = ['zone', 'fiscal_year', 'base_billing_day', 'month']


@admin.register(BillingSummary)
class BillingSummaryAdmin(admin.ModelAdmin):
    list_display = [
        'meter', 'project_id', 'project_name', 'zone',
        'period_start', 'period_end',
        'actual_kwh', 'deemed_kwh', 'total_kwh',
        'deemed_method', 'fetch_status', 'created_at'
    ]
    list_filter = ['zone', 'deemed_method', 'fetch_status', 'is_first_billing']
    search_fields = ['meter__meter_id', 'project_id', 'project_name']
    date_hierarchy = 'period_end'
    readonly_fields = ['created_at', 'updated_at']
    
    actions = ['reset_to_pending', 'retry_errors']
    
    @admin.action(description='選択したデータをpendingに戻す')
    def reset_to_pending(self, request, queryset):
        count = queryset.update(
            fetch_status='pending',
            fetch_started_at=None,
            fetch_completed_at=None,
            fetch_error_message=''
        )
        self.message_user(request, f'{count}件をpendingに戻しました')
    
    @admin.action(description='エラーデータをリトライ')
    def retry_errors(self, request, queryset):
        count = queryset.filter(fetch_status='error').update(
            fetch_status='pending',
            fetch_started_at=None,
            fetch_completed_at=None,
            fetch_error_message=''
        )
        self.message_user(request, f'{count}件をpendingに戻しました')