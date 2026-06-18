from django.contrib import admin
from .infrastructure.models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('dni', 'first_name', 'last_name', 'role', 'support_role', 'is_active')
    search_fields = ('dni', 'first_name', 'last_name')
    list_filter = ('role', 'support_role', 'is_active')
    ordering = ('role', 'last_name')