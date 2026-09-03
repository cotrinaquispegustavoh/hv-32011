from django.urls import path
from .interfaces.views import dashboard_views, public_views, calendar_views

app_name = 'core'

urlpatterns = [
    path('', public_views.home_view, name='home'),
    path('dashboard/', dashboard_views.dashboard_view, name='dashboard'),
    path('notificaciones/', dashboard_views.notifications_view, name='notifications'),
    path('notificaciones/leer/', dashboard_views.mark_notifications_read_view, name='mark_notifications_read'),
    path('notificaciones/ir/<int:notif_id>/', dashboard_views.read_notification_view, name='read_notification'),
    path('notificaciones/<int:notif_id>/estado/', dashboard_views.update_notification_state_view, name='update_notification_state'),
    path('actividad/', dashboard_views.activity_view, name='activity'),
    path('calendario/', calendar_views.calendar_view, name='calendar'),
    path('calendario/nueva-fecha/', calendar_views.create_event_view, name='create_event'),
    path('calendario/nuevo-comunicado/', calendar_views.create_announcement_view, name='create_announcement'),
    path('api/calendario/', calendar_views.api_calendar_events, name='api_calendar'),
    path('comunicados/<int:announcement_id>/', calendar_views.announcement_detail_view, name='announcement_detail'),
    path('comunicados/<int:announcement_id>/confirmar/', calendar_views.acknowledge_announcement_view, name='acknowledge_announcement'),
    path('comunicados/<int:announcement_id>/publicacion/', calendar_views.toggle_announcement_view, name='toggle_announcement'),
]
