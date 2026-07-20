from django.urls import path
from .interfaces.views import parent_views

app_name = 'academics'

urlpatterns = [
    path('apoderado/', parent_views.parent_dashboard_view, name='parent_dashboard'),
    path('apoderado/hijo/<int:student_id>/', parent_views.child_detail_view, name='child_detail'),
]