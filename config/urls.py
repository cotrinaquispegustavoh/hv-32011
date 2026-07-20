from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('hv-admin/', admin.site.urls),
    
    path('auth/', include('apps.users.urls')),
    path('almacen/', include('apps.warehouse.urls')),
    path('disciplina/', include('apps.discipline.urls')),
    path('portafolio/', include('apps.portfolio.urls')),
    path('documentos/', include('apps.documents.urls')),
    path('asignaciones/', include('apps.assignments.urls')),
    path('academico/', include('apps.academics.urls')),
    path('', include('apps.core.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)