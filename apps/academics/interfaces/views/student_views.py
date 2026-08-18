from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from apps.academics.infrastructure.repositories.academics_repository import DjangoStudentRepository
from apps.academics.core.use_cases.manage_students import GetStudentDirectoryUseCase
from apps.core.utils import normalize_text # <-- IMPORTAR

@login_required(login_url='/auth/login/')
def student_directory_view(request):
    if request.user.role not in ['DIRECTOR', 'SUBDIRECTOR', 'SUPERUSER', 'APOYO']:
        return redirect('core:dashboard')
    repo = DjangoStudentRepository()
    students = GetStudentDirectoryUseCase(repo).execute()
    sections = sorted(list(set(s.section_name for s in students if s.section_name != "Sin sección")))
    return render(request, 'academics/student_directory.html', {'students': students, 'sections': sections})

@login_required(login_url='/auth/login/')
def search_students_view(request):
    # Normalizamos la búsqueda (ej. "gómez" -> "gomez")
    query = normalize_text(request.GET.get('q', ''))
    section = request.GET.get('section', '')
    
    repo = DjangoStudentRepository()
    students = GetStudentDirectoryUseCase(repo).execute()
    
    if query:
        # Normalizamos los campos antes de comparar
        students = [s for s in students if query in normalize_text(s.first_name) or query in normalize_text(s.last_name) or query in normalize_text(s.dni)]
    if section:
        students = [s for s in students if s.section_name == section]
        
    return render(request, 'academics/partials/student_table_rows.html', {'students': students})