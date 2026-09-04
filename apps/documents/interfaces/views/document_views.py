from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.files.storage import default_storage
from apps.core.file_validation import UploadValidationError, validate_document_upload
from apps.documents.infrastructure.repositories.document_repository import DjangoDocumentRepository
from apps.documents.core.use_cases.manage_documents import GetAccessibleDocumentsUseCase, UploadDocumentUseCase, UpdateDocumentUseCase, DeleteDocumentUseCase
from apps.users.interfaces.middlewares import require_permission

@login_required(login_url='/auth/login/')
@require_permission('documents.view')
def document_list_view(request):
    repo = DjangoDocumentRepository()
    documents = GetAccessibleDocumentsUseCase(repo).execute(request.user.role)
    categories = repo.get_all_categories()
    return render(request, 'documents/list.html', {'documents': documents, 'categories': categories})

@login_required(login_url='/auth/login/')
@require_permission('documents.view')
def search_documents_view(request):
    query = request.GET.get('q', '').lower()
    category_id = request.GET.get('category_id', '')
    repo = DjangoDocumentRepository()
    documents = GetAccessibleDocumentsUseCase(repo).execute(request.user.role)
    
    if query:
        documents = [d for d in documents if query in d.title.lower() or query in d.tags.lower()]
    if category_id:
        documents = [d for d in documents if str(d.category_id) == category_id]
        
    return render(request, 'documents/partials/document_table.html', {'documents': documents})

@login_required(login_url='/auth/login/')
@require_permission('documents.manage')
def manage_categories_view(request):
    repo = DjangoDocumentRepository()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            name = request.POST.get('name')
            if name:
                repo.create_category(name)
                messages.success(request, f'Categoría "{name}" creada.')
        elif action == 'edit':
            cat_id = request.POST.get('category_id')
            new_name = request.POST.get('name')
            if cat_id and new_name:
                repo.update_category(int(cat_id), new_name)
                messages.success(request, 'Categoría actualizada correctamente.')
        elif action == 'delete':
            cat_id = request.POST.get('category_id')
            if cat_id:
                try:
                    repo.delete_category(int(cat_id))
                    messages.success(request, 'Categoría eliminada.')
                except ValueError as e:
                    messages.error(request, str(e))
        return redirect('documents:manage_categories')

    categories = repo.get_all_categories()
    return render(request, 'documents/manage_categories.html', {'categories': categories})

@login_required(login_url='/auth/login/')
@require_permission('documents.publish')
def upload_document_view(request):
    repo = DjangoDocumentRepository()

    if request.method == 'POST':
        title = request.POST.get('title')
        category_id = request.POST.get('category_id')
        access_level = request.POST.get('access_level')
        tags = request.POST.get('tags', '')
        
        if 'file' in request.FILES:
            file = request.FILES['file']
            try:
                validate_document_upload(file)
            except UploadValidationError as e:
                messages.error(request, str(e))
                return redirect('documents:upload')

            file_path = default_storage.save(f'institutional_docs/{file.name}', file)

            try:
                UploadDocumentUseCase(repo).execute(title, int(category_id), access_level, tags, file_path, request.user.id)
                messages.success(request, 'Documento publicado exitosamente.')
                return redirect('documents:list')
            except Exception as e:
                default_storage.delete(file_path)
                messages.error(request, f'Error al subir: {str(e)}')
        else:
            messages.error(request, 'Debes adjuntar un archivo.')

    categories = repo.get_all_categories()
    return render(request, 'documents/upload.html', {'categories': categories})

# --- NUEVAS VISTAS: EDITAR Y ELIMINAR ---
@login_required(login_url='/auth/login/')
@require_permission('documents.publish')
def edit_document_view(request, document_id):
    repo = DjangoDocumentRepository()
    doc = repo.get_by_id(document_id)
    
    if not doc:
        messages.error(request, "Documento no encontrado.")
        return redirect('documents:list')

    if request.method == 'POST':
        title = request.POST.get('title')
        category_id = request.POST.get('category_id')
        access_level = request.POST.get('access_level')
        tags = request.POST.get('tags', '')
        
        file_path = None
        if 'file' in request.FILES:
            file = request.FILES['file']
            try:
                validate_document_upload(file)
            except UploadValidationError as e:
                messages.error(request, str(e))
                return redirect('documents:edit', document_id=document_id)
            file_path = default_storage.save(f'institutional_docs/{file.name}', file)

        try:
            UpdateDocumentUseCase(repo).execute(document_id, title, int(category_id), access_level, tags, file_path)
            messages.success(request, 'Documento actualizado exitosamente.')
            return redirect('documents:list')
        except Exception as e:
            if file_path:
                default_storage.delete(file_path)
            messages.error(request, f'Error al actualizar: {str(e)}')

    categories = repo.get_all_categories()
    return render(request, 'documents/edit.html', {'doc': doc, 'categories': categories})

@login_required(login_url='/auth/login/')
@require_permission('documents.manage')
def delete_document_view(request, document_id):
    if request.method == 'POST':
        repo = DjangoDocumentRepository()
        DeleteDocumentUseCase(repo).execute(document_id)
        return HttpResponse("") # HTMX elimina la fila visualmente
    return HttpResponse("Método no permitido", status=405)
