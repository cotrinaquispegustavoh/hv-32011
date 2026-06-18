from django.contrib import admin
from .infrastructure.models import PortfolioItem, Observation

@admin.register(PortfolioItem)
class PortfolioItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'item_type', 'teacher', 'created_at')
    list_filter = ('item_type', 'created_at')
    search_fields = ('title', 'teacher__first_name', 'teacher__last_name')
    date_hierarchy = 'created_at'

admin.site.register(Observation)