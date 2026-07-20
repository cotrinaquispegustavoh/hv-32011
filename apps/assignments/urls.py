from django.urls import path
from .interfaces.views import assignment_views

app_name = 'assignments'

urlpatterns = [
    path('', assignment_views.assignment_panel_view, name='panel'),
    path('eliminar/<int:assignment_id>/', assignment_views.remove_assignment_view, name='remove'),
]