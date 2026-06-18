from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('apps.users.urls')),
    path('almacen/', include('apps.warehouse.urls')),
    path('disciplina/', include('apps.discipline.urls')),
    path('portafolio/', include('apps.portfolio.urls')),
    path('', include('apps.core.urls')),
]