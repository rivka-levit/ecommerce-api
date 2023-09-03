from django.contrib import admin

from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['email', 'name']
    fields = ['email', 'name', 'id', 'last_login', 'is_active', 'is_superuser',
              'is_staff', 'groups', 'user_permissions', 'password']
    readonly_fields = ['password', 'id', 'last_login']
    list_filter = ['is_active', 'is_staff']
