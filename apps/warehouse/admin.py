from django.contrib import admin
from .infrastructure.models import Material, LoanRequest, LoanDetail

@admin.action(description="Mover a la papelera (Soft Delete)")
def soft_delete_action(modeladmin, request, queryset):
    for obj in queryset:
        obj.delete()

# --- NUEVA ACCIÓN: HARD DELETE ---
@admin.action(description="⚠️ Destruir permanentemente (Hard Delete)")
def hard_delete_action(modeladmin, request, queryset):
    for obj in queryset:
        obj.delete(hard=True) # Esto borra el registro de la base de datos real

@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ('name', 'stock', 'unit', 'state', 'cycle', 'location', 'is_deleted')
    search_fields = ('name', 'location')
    list_filter = ('cycle', 'state', 'is_deleted')
    
    # Añadimos ambas acciones al menú
    actions = [soft_delete_action, hard_delete_action]
    
    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def get_queryset(self, request):
        return self.model.all_objects.all()

@admin.register(LoanRequest)
class LoanRequestAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'status', 'request_date', 'is_deleted')
    list_filter = ('status', 'is_deleted')
    actions = [soft_delete_action, hard_delete_action]
    
    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def get_queryset(self, request):
        return self.model.all_objects.all()

admin.site.register(LoanDetail)