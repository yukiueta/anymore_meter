from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'permission', 'is_active', 'date_joined']
    list_filter = ['permission', 'is_active']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('追加情報', {'fields': ('permission',)}),
    )