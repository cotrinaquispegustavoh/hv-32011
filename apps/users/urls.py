from django.urls import path
from .interfaces.views import auth_views, staff_views

app_name = 'users'

urlpatterns = [
    path('login/', auth_views.login_view, name='login'),
    path('logout/', auth_views.logout_view, name='logout'),
    path('cambiar-password/', auth_views.password_change_view, name='password_change'),
    path('personal/', staff_views.staff_list_view, name='staff_list'),
    path('personal/estado/<int:user_id>/', staff_views.toggle_status_view, name='toggle_status'),
    path('personal/buscar/', staff_views.search_staff_view, name='search_staff'),
    path('personal/permisos/bloque/', staff_views.bulk_permissions_view, name='bulk_permissions'),
]