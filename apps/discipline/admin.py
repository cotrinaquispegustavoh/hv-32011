from django.contrib import admin
from .infrastructure.models import Incident, Evidence

@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ('student', 'severity', 'subtype', 'reported_by', 'date_reported')
    list_filter = ('severity', 'subtype', 'date_reported')
    search_fields = ('student__first_name', 'student__last_name', 'description')
    date_hierarchy = 'date_reported'

admin.site.register(Evidence)