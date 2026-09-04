from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.files.storage import default_storage
from apps.core.file_validation import UploadValidationError, validate_portfolio_upload
from apps.users.interfaces.middlewares import require_permission
from apps.portfolio.infrastructure.repositories.portfolio_repository import DjangoPortfolioRepository
from apps.portfolio.core.use_cases.manage_portfolio import UploadPortfolioItemUseCase
from django.http import HttpResponse
from apps.portfolio.infrastructure.repositories.portfolio_repository import DjangoObservationRepository
from apps.portfolio.core.use_cases.manage_portfolio import GetAllPortfolioItemsUseCase, AddObservationUseCase

@login_required(login_url='/auth/login/')
@require_permission('portfolio.own')
def portfolio_list_view(request):
    repo = DjangoPortfolioRepository()
    items = repo.get_by_teacher(request.user.id)
    return render(request, 'portfolio/list.html', {'items': items})

@login_required(login_url='/auth/login/')
@require_permission('portfolio.own')
def upload_item_view(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        item_type = request.POST.get('item_type')
        description = request.POST.get('description', '')
        
        if 'file' in request.FILES:
            file = request.FILES['file']
            try:
                validate_portfolio_upload(file)
            except UploadValidationError as e:
                messages.error(request, str(e))
                return redirect('portfolio:upload')

            file_path = default_storage.save(f'portfolio_files/{file.name}', file)

            repo = DjangoPortfolioRepository()
            use_case = UploadPortfolioItemUseCase(repo)
            
            try:
                use_case.execute(
                    teacher_id=request.user.id,
                    item_type=item_type,
                    title=title,
                    description=description,
                    file_path=file_path
                )
                messages.success(request, 'Ficha subida exitosamente al portafolio.')
                return redirect('portfolio:list')
            except Exception as e:
                default_storage.delete(file_path)
                messages.error(request, f'Error al subir: {str(e)}')
                return redirect('portfolio:upload')
        else:
            messages.error(request, 'Debes adjuntar un archivo.')
            return redirect('portfolio:upload')

    return render(request, 'portfolio/upload.html')

@login_required(login_url='/auth/login/')
@require_permission('portfolio.review')
def portfolio_review_view(request):
    repo = DjangoPortfolioRepository()
    use_case = GetAllPortfolioItemsUseCase(repo)
    items = use_case.execute()
    
    return render(request, 'portfolio/review_panel.html', {'items': items})

@login_required(login_url='/auth/login/')
@require_permission('portfolio.review')
def add_observation_view(request, item_id):
    if request.method == 'POST':
        content = request.POST.get('content')
        
        repo = DjangoObservationRepository()
        use_case = AddObservationUseCase(repo)
        
        try:
            use_case.execute(item_id, request.user.id, content)
            # HTMX: Ordenamos recargar la página para ver la nueva observación
            response = HttpResponse()
            response['HX-Refresh'] = 'true'
            return response
        except ValueError as e:
            return HttpResponse(f'<span class="text-red-600 text-xs font-bold">{str(e)}</span>')
            
    return HttpResponse("Método no permitido", status=405)
