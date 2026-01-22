from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'username', 'permission', 'is_active', 'date_joined']
    list_filter = ['permission', 'is_active']
    search_fields = ['email', 'username']
    ordering = ['-id']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('権限', {'fields': ('permission',)}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('権限', {'fields': ('permission',)}),
    )