from django.urls import path
from .interfaces.views import parent_views, student_views

app_name = 'academics'

urlpatterns = [
    # Rutas del Apoderado
    path('apoderado/', parent_views.parent_dashboard_view, name='parent_dashboard'),
    path('apoderado/hijo/<int:student_id>/', parent_views.child_detail_view, name='child_detail'),
    
    # Rutas del Directorio (Directivos)
    path('directorio/', student_views.student_directory_view, name='student_directory'),
    path('directorio/buscar/', student_views.search_students_view, name='search_students'),
]