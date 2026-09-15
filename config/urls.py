from django.contrib import admin
from django.urls import path, include, re_path
from apps.core.interfaces.views.media_views import protected_media_view

urlpatterns = [
    path('django-admin/', admin.site.urls),
    
    path('auth/', include('apps.users.urls')),
    path('almacen/', include('apps.warehouse.urls')),
    path('disciplina/', include('apps.discipline.urls')),
    path('portafolio/', include('apps.portfolio.urls')),
    path('documentos/', include('apps.documents.urls')),
    path('asignaciones/', include('apps.assignments.urls')),
    path('academico/', include('apps.academics.urls')),
    path('', include('apps.core.urls')),
    
    # Conserva las URLs actuales, pero exige autenticación y permiso antes de
    # entregar cualquier archivo subido.
    re_path(r'^media/(?P<path>.*)$', protected_media_view, name='protected_media'),
]
