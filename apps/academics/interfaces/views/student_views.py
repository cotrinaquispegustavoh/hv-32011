import csv
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from apps.users.infrastructure.repositories.user_repository import DjangoUserRepository
from apps.academics.infrastructure.repositories.academics_repository import DjangoSectionRepository, DjangoParentRepository, DjangoStudentRepository
from apps.academics.core.use_cases.import_students import ImportStudentsUseCase
from apps.academics.core.use_cases.manage_students import GetStudentDirectoryUseCase
from apps.core.utils import normalize_text
from django.http import HttpResponseForbidden

@login_required(login_url='/auth/login/')
def student_directory_view(request):
    # CORRECCIÓN: Permitimos el acceso a DOCENTES
    if request.user.role not in ['DIRECTOR', 'SUBDIRECTOR', 'SUPERUSER', 'APOYO', 'DOCENTE']:
        return redirect('core:dashboard')
    
    repo = DjangoStudentRepository()

    if request.method == 'POST' and request.POST.get('action') == 'csv_upload':
        if request.user.role not in ['DIRECTOR', 'SUBDIRECTOR', 'SUPERUSER']:
            return HttpResponseForbidden("No tienes permiso para importar matrículas.")

        if 'csv_file' not in request.FILES:
            messages.error(request, 'Debes adjuntar un archivo CSV.')
            return redirect('academics:student_directory')
            
        csv_file = request.FILES['csv_file']
        user_repo = DjangoUserRepository()
        section_repo = DjangoSectionRepository()
        parent_repo = DjangoParentRepository()
        use_case = ImportStudentsUseCase(user_repo, section_repo, parent_repo, repo)
        
        creados, errores = 0, []
        current_year = timezone.now().year

        try:
            decoded_file = csv_file.read().decode('utf-8-sig').splitlines()
            delimiter = ';'
            if decoded_file and '\t' in decoded_file[0]: delimiter = '\t'
            elif decoded_file and ';' not in decoded_file[0] and ',' in decoded_file[0]: delimiter = ','

            reader = csv.DictReader(decoded_file, delimiter=delimiter)
            if reader.fieldnames:
                reader.fieldnames = [str(c).strip().lower().replace(' ', '_') for c in reader.fieldnames if c]

            with transaction.atomic():
                for idx, row in enumerate(reader, start=2):
                    try:
                        use_case.execute(row, current_year)
                        creados += 1
                    except ValueError as ve:
                        errores.append(f"Fila {idx}: {str(ve)}")
                        
            messages.success(request, f'Importación exitosa: {creados} alumnos matriculados.')
            if errores:
                for err in errores[:5]: messages.error(request, err)
        except Exception as e:
            messages.error(request, f'Error al procesar el archivo: {str(e)}')
            
        return redirect('academics:student_directory')

    students = GetStudentDirectoryUseCase(repo).execute()
    
    # CORRECCIÓN: Si es docente, filtramos solo sus alumnos
    if request.user.role == 'DOCENTE':
        from apps.assignments.infrastructure.models import TeacherAssignment
        assigned_sections = TeacherAssignment.objects.filter(teacher_id=request.user.id, academic_year=timezone.now().year).values_list('section_id', flat=True)
        students = [s for s in students if s.section_id in assigned_sections]

    sections = sorted(list(set(s.section_name for s in students if s.section_name != "Sin sección")))
    
    return render(request, 'academics/student_directory.html', {'students': students, 'sections': sections})

@login_required(login_url='/auth/login/')
def search_students_view(request):
    if request.user.role not in ['DIRECTOR', 'SUBDIRECTOR', 'SUPERUSER', 'APOYO', 'DOCENTE']:
        return HttpResponseForbidden()

    query = normalize_text(request.GET.get('q', ''))
    section = request.GET.get('section', '')
    
    repo = DjangoStudentRepository()
    students = GetStudentDirectoryUseCase(repo).execute()
    
    if request.user.role == 'DOCENTE':
        from apps.assignments.infrastructure.models import TeacherAssignment
        assigned_sections = TeacherAssignment.objects.filter(teacher_id=request.user.id, academic_year=timezone.now().year).values_list('section_id', flat=True)
        students = [s for s in students if s.section_id in assigned_sections]
    
    if query:
        students = [s for s in students if query in normalize_text(s.first_name) or query in normalize_text(s.last_name) or query in normalize_text(s.dni)]
    if section:
        students = [s for s in students if s.section_name == section]
        
    return render(request, 'academics/partials/student_table_rows.html', {'students': students})
