from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.documents.infrastructure.repositories.document_repository import DjangoDocumentRepository
from apps.documents.core.use_cases.manage_documents import GetAccessibleDocumentsUseCase

@login_required(login_url='/auth/login/')
def document_list_view(request):
    repo = DjangoDocumentRepository()
    use_case = GetAccessibleDocumentsUseCase(repo)
    
    documents = use_case.execute(request.user.role)
    
    return render(request, 'documents/list.html', {'documents': documents})