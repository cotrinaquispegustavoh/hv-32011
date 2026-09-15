from django.urls import path
from .interfaces.views import incident_views

app_name = 'discipline'

urlpatterns = [
    path('reportar/', incident_views.report_incident_view, name='report_incident'),
    path('api/estudiantes/', incident_views.student_search_view, name='student_search'),
    path('api/secciones/', incident_views.section_search_view, name='section_search'),
    path('historial/', incident_views.incident_list_view, name='incident_list'),
    path('buscar/', incident_views.search_incidents_view, name='search_incidents'), 
]
