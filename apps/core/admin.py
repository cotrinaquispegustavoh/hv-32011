from django.contrib import admin
from .infrastructure.models import AuditLog, InternalNotification, InstitutionalEvent

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    # Mostramos las columnas clave en la lista
    list_display = ('action', 'model_name', 'user', 'timestamp', 'ip_address')
    
    # Filtros laterales muy útiles para auditoría
    list_filter = ('action', 'model_name', 'timestamp')
    
    # Buscador por usuario o ID de objeto
    search_fields = ('user__first_name', 'user__last_name', 'user__dni', 'object_id')
    
    # La auditoría es de solo lectura (nadie debería poder alterar el historial)
    readonly_fields = ('user', 'action', 'model_name', 'object_id', 'changes', 'timestamp', 'ip_address')
    
    def has_add_permission(self, request):
        return False # Nadie puede crear logs a mano
        
    def has_change_permission(self, request, obj=None):
        return False # Nadie puede editar logs
        
    def has_delete_permission(self, request, obj=None):
        return False # Nadie puede borrar logs

@admin.register(InstitutionalEvent)
class InstitutionalEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'event_date', 'is_holiday')
    list_filter = ('is_holiday', 'event_date')
    search_fields = ('title', 'description')
    date_hierarchy = 'event_date'

@admin.register(InternalNotification)
class InternalNotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('user__dni', 'title')