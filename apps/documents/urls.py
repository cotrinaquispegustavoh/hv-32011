from django.urls import path
from .interfaces.views import document_views

app_name = 'documents'

urlpatterns = [
    path('', document_views.document_list_view, name='list'),
]