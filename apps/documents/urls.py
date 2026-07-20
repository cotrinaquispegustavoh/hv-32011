from django.urls import path
from .interfaces.views import document_views

app_name = 'documents'

urlpatterns = [
    path('', document_views.document_list_view, name='list'),
    path('subir/', document_views.upload_document_view, name='upload'),
    path('buscar/', document_views.search_documents_view, name='search'),
    path('categorias/', document_views.manage_categories_view, name='manage_categories'),
    path('editar/<int:document_id>/', document_views.edit_document_view, name='edit'), # <-- NUEVA
    path('eliminar/<int:document_id>/', document_views.delete_document_view, name='delete'), # <-- NUEVA
]