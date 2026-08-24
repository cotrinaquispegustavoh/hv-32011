from django.contrib import admin
from .infrastructure.models import PortfolioItem, Observation

@admin.action(description="Mover a la papelera (Soft Delete)")
def soft_delete_action(modeladmin, request, queryset):
    for obj in queryset:
        obj.delete()

# --- NUEVA ACCIÓN: HARD DELETE ---
@admin.action(description="⚠️ Destruir permanentemente (Hard Delete)")
def hard_delete_action(modeladmin, request, queryset):
    for obj in queryset:
        obj.delete(hard=True) # Borra el registro de la base de datos real

@admin.register(PortfolioItem)
class PortfolioItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'item_type', 'teacher', 'created_at', 'is_deleted')
    list_filter = ('item_type', 'created_at', 'is_deleted')
    search_fields = ('title', 'teacher__first_name', 'teacher__last_name')
    date_hierarchy = 'created_at'
    
    # Añadimos ambas acciones al menú
    actions = [soft_delete_action, hard_delete_action]
    
    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def get_queryset(self, request):
        return self.model.all_objects.all()

admin.site.register(Observation)