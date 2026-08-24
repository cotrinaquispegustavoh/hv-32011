from django.urls import path
from .interfaces.views import dashboard_views, public_views

app_name = 'core'

urlpatterns = [
    path('', public_views.home_view, name='home'), # El landing page es la raíz
    path('dashboard/', dashboard_views.dashboard_view, name='dashboard'), # Movimos el dashboard aquí
    path('notificaciones/leer/', dashboard_views.mark_notifications_read_view, name='mark_notifications_read'),
    path('notificaciones/ir/<int:notif_id>/', dashboard_views.read_notification_view, name='read_notification'),

]