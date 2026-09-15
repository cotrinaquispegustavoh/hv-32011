from django.contrib import admin
from .infrastructure.models import Incident, Evidence

@admin.action(description="Mover a la papelera (Soft Delete)")
def soft_delete_action(modeladmin, request, queryset):
    for obj in queryset:
        obj.delete()

# --- NUEVA ACCIÓN: HARD DELETE ---
@admin.action(description="⚠️ Destruir permanentemente (Hard Delete)")
def hard_delete_action(modeladmin, request, queryset):
    for obj in queryset:
        obj.delete(hard=True) # Borra el registro de la base de datos real

@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ('code', 'student', 'category', 'subtype', 'severity', 'reported_by', 'occurred_at', 'status', 'is_deleted')
    list_filter = ('category', 'subtype', 'severity', 'status', 'requires_follow_up', 'occurred_at', 'is_deleted')
    search_fields = ('code', 'student__dni', 'student__first_name', 'student__last_name', 'description')
    date_hierarchy = 'occurred_at'
    readonly_fields = ('code', 'academic_year', 'date_reported', 'updated_at')
    
    # Añadimos ambas acciones al menú
    actions = [soft_delete_action, hard_delete_action]
    
    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def get_queryset(self, request):
        return self.model.all_objects.all()

admin.site.register(Evidence)
