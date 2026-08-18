from django.urls import path
from .interfaces.views import auth_views, staff_views

app_name = 'users'

urlpatterns = [
    path('login/', auth_views.login_view, name='login'),
    path('logout/', auth_views.logout_view, name='logout'),
    path('cambiar-password/', auth_views.password_change_view, name='password_change'),
    
    path('personal/', staff_views.staff_list_view, name='staff_list'),
    path('personal/buscar/', staff_views.search_staff_view, name='search_staff'),
    
    path('personal/detalle/<int:user_id>/', staff_views.staff_detail_view, name='staff_detail'),
    path('personal/permiso/toggle/<int:user_id>/', staff_views.toggle_module_permission_view, name='toggle_permission'),
    path('personal/estado/<int:user_id>/', staff_views.toggle_status_view, name='toggle_status'),
]