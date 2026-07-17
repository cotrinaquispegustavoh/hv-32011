from django.contrib import admin
from .infrastructure.models import AuditLog, InternalNotification, InstitutionalEvent

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    # CORRECCIÓN: Usamos un método personalizado en lugar de la palabra reservada 'action'
    list_display = ('get_action_label', 'model_name', 'user', 'timestamp', 'ip_address')
    list_filter = ('action', 'model_name', 'timestamp')
    search_fields = ('user__first_name', 'user__last_name', 'user__dni', 'object_id')
    readonly_fields = ('user', 'action', 'model_name', 'object_id', 'changes', 'timestamp', 'ip_address')
    
    @admin.display(description='Acción Realizada')
    def get_action_label(self, obj):
        return obj.get_action_display() # Esto mostrará "Inicio de Sesión" en lugar de "LOGIN"
    
    def has_add_permission(self, request):
        return False 
        
    def has_change_permission(self, request, obj=None):
        return False 
        
    def has_delete_permission(self, request, obj=None):
        return False 

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