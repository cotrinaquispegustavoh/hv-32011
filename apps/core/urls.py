from django.urls import path
from .interfaces.views import dashboard_views, public_views

app_name = 'core'

urlpatterns = [
    path('', public_views.home_view, name='home'), # El landing page es la raíz
    path('dashboard/', dashboard_views.dashboard_view, name='dashboard'), # Movimos el dashboard aquí
]