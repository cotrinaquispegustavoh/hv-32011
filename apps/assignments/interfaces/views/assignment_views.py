import csv
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from apps.assignments.infrastructure.repositories.assignment_repository import DjangoTeacherAssignmentRepository
from apps.assignments.core.use_cases.manage_assignments import AssignTeacherUseCase, RemoveAssignmentUseCase, GetTeacherAssignmentsUseCase
from apps.assignments.core.use_cases.import_assignments import ImportAssignmentsUseCase
from apps.users.infrastructure.models import User
from apps.academics.infrastructure.models import Section
from apps.assignments.infrastructure.models import TeacherAssignment

@login_required(login_url='/auth/login/')
def assignment_panel_view(request):
    if request.user.role not in ['DIRECTOR', 'SUPERUSER']:
        return redirect('core:dashboard')

    current_year = timezone.now().year
    teachers = User.objects.filter(role='DOCENTE', is_active=True).order_by('last_name')
    sections = Section.objects.filter(year=current_year).order_by('grade', 'letter')
    assignments = TeacherAssignment.objects.filter(academic_year=current_year).select_related('teacher', 'section').order_by('section__grade', 'section__letter')

    if request.method == 'POST':
        action = request.POST.get('action')
        repo = DjangoTeacherAssignmentRepository()

        if action == 'manual':
            teacher_id = request.POST.get('teacher_id')
            section_ids = request.POST.getlist('section_ids')
            area = request.POST.get('area')
            
            section_ids_int = [int(sid) for sid in section_ids if sid.isdigit()]
            if not section_ids_int:
                messages.error(request, 'Debes seleccionar al menos un aula.')
                return redirect('assignments:panel')

            use_case = AssignTeacherUseCase(repo)
            try:
                use_case.execute(int(teacher_id), section_ids_int, area, current_year)
                messages.success(request, f'Se crearon {len(section_ids_int)} asignaciones correctamente.')
            except Exception as e:
                messages.error(request, 'Error: Una de las asignaciones ya existe o los datos son inválidos.')
            return redirect('assignments:panel')

        elif action == 'csv_upload':
            if 'csv_file' not in request.FILES:
                messages.error(request, 'Debes adjuntar un archivo CSV.')
                return redirect('assignments:panel')
                
            csv_file = request.FILES['csv_file']
            use_case = ImportAssignmentsUseCase(repo)
            creados = 0
            errores = []

            try:
                decoded_file = csv_file.read().decode('utf-8-sig').splitlines()
                
                # CORRECCIÓN: Detector automático de separador (Tabulación, Coma o Punto y Coma)
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
                            
                if creados > 0:
                    messages.success(request, f'Se importaron {creados} asignaciones con éxito.')
                if errores:
                    for err in errores[:5]:
                        messages.error(request, err)
                        
            except Exception as e:
                messages.error(request, f'Error al procesar el archivo: {str(e)}')
                
            return redirect('assignments:panel')

    context = {
        'teachers': teachers,
        'sections': sections,
        'assignments': assignments,
        'current_year': current_year
    }
    return render(request, 'assignments/panel.html', context)

@login_required(login_url='/auth/login/')
def remove_assignment_view(request, assignment_id):
    if request.method == 'POST' and request.user.role in ['DIRECTOR', 'SUPERUSER']:
        repo = DjangoTeacherAssignmentRepository()
        use_case = RemoveAssignmentUseCase(repo)
        use_case.execute(assignment_id)
        return HttpResponse("") 
    return HttpResponse("No autorizado", status=403)

@login_required(login_url='/auth/login/')
def my_sections_view(request):
    if request.user.role != 'DOCENTE':
        return redirect('core:dashboard')
    repo = DjangoTeacherAssignmentRepository()
    use_case = GetTeacherAssignmentsUseCase(repo)
    current_year = timezone.now().year
    assignments = use_case.execute(request.user.id, current_year)
    return render(request, 'assignments/my_sections.html', {'assignments': assignments, 'current_year': current_year})