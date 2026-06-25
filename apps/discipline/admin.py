from django.contrib import admin
from .infrastructure.models import Incident, Evidence

@admin.action(description="Mover a la papelera (Soft Delete)")
def soft_delete_action(modeladmin, request, queryset):
    for obj in queryset:
        obj.delete()

@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ('student', 'severity', 'subtype', 'reported_by', 'date_reported', 'is_deleted')
    list_filter = ('severity', 'subtype', 'date_reported', 'is_deleted')
    search_fields = ('student__first_name', 'student__last_name', 'description')
    date_hierarchy = 'date_reported'
    
    actions = [soft_delete_action]
    
    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def get_queryset(self, request):
        return self.model.all_objects.all()

admin.site.register(Evidence)