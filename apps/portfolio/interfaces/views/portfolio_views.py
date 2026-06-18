from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from apps.users.interfaces.middlewares import require_module_permission
from apps.portfolio.infrastructure.repositories.portfolio_repository import DjangoPortfolioRepository
from apps.portfolio.core.use_cases.manage_portfolio import UploadPortfolioItemUseCase
import os

@login_required(login_url='/auth/login/')
@require_module_permission('portafolio')
def portfolio_list_view(request):
    repo = DjangoPortfolioRepository()
    items = repo.get_by_teacher(request.user.id)
    return render(request, 'portfolio/list.html', {'items': items})

@login_required(login_url='/auth/login/')
@require_module_permission('portafolio')
def upload_item_view(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        item_type = request.POST.get('item_type')
        description = request.POST.get('description', '')
        
        if 'file' in request.FILES:
            file = request.FILES['file']
            
            # VALIDACIÓN BACKEND ESTRICTA
            if file.size > 10485760: # 10MB
                messages.error(request, 'El archivo excede los 10MB permitidos.')
                return redirect('portfolio:upload')

            ext = os.path.splitext(file.name)[1].lower()
            allowed_extensions = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png']
            if ext not in allowed_extensions:
                messages.error(request, f'Formato no permitido ({ext}). Solo PDF, Word o Imágenes.')
                return redirect('portfolio:upload')

            fs = FileSystemStorage(location='media/portfolio_files/')
            filename = fs.save(file.name, file)
            file_path = f'portfolio_files/{filename}'

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
                messages.error(request, f'Error al subir: {str(e)}')
                return redirect('portfolio:upload')
        else:
            messages.error(request, 'Debes adjuntar un archivo.')
            return redirect('portfolio:upload')

    return render(request, 'portfolio/upload.html')