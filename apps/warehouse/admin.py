from django.contrib import admin
from .infrastructure.models import Material, LoanRequest, LoanDetail

@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ('name', 'stock', 'unit', 'state', 'cycle', 'location')
    search_fields = ('name', 'location')
    list_filter = ('cycle', 'state')

# Registramos también las solicitudes para verlas más adelante
admin.site.register(LoanRequest)
admin.site.register(LoanDetail)