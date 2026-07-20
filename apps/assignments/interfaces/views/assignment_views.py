import csv
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from apps.assignments.infrastructure.repositories.assignment_repository import DjangoTeacherAssignmentRepository
from apps.assignments.core.use_cases.manage_assignments import AssignTeacherUseCase, RemoveAssignmentUseCase
from apps.assignments.core.use_cases.import_assignments import ImportAssignmentsUseCase
from apps.users.infrastructure.models import User
from apps.academics.infrastructure.models import Section
from apps.assignments.infrastructure.models import TeacherAssignment

@login_required(login_url='/auth/login/')
def assignment_panel_view(request):
    if request.user.role not in ['DIRECTOR', 'SUPERUSER']:
        return redirect('core:dashboard')

    teachers = User.objects.filter(role='DOCENTE', is_active=True).order_by('last_name')
    sections = Section.objects.filter(year=2026).order_by('grade', 'letter')
    assignments = TeacherAssignment.objects.filter(academic_year=2026).select_related('teacher', 'section').order_by('section__grade', 'section__letter')

    if request.method == 'POST':
        action = request.POST.get('action')
        repo = DjangoTeacherAssignmentRepository()

        # --- ASIGNACIÓN MANUAL (MÚLTIPLE) ---
        if action == 'manual':
            teacher_id = request.POST.get('teacher_id')
            section_ids = request.POST.getlist('section_ids') # Capturamos la lista de checkboxes
            area = request.POST.get('area')
            
            # Convertimos los IDs a enteros
            section_ids_int = [int(sid) for sid in section_ids if sid.isdigit()]
            
            if not section_ids_int:
                messages.error(request, 'Debes seleccionar al menos un aula.')
                return redirect('assignments:panel')

            use_case = AssignTeacherUseCase(repo)
            try:
                use_case.execute(int(teacher_id), section_ids_int, area, 2026)
                messages.success(request, f'Se crearon {len(section_ids_int)} asignaciones correctamente.')
            except Exception as e:
                messages.error(request, 'Error: Una de las asignaciones ya existe o los datos son inválidos.')
            return redirect('assignments:panel')

        # --- CARGA MASIVA (CSV) ---
        elif action == 'csv_upload':
            if 'csv_file' not in request.FILES:
                messages.error(request, 'Debes adjuntar un archivo CSV.')
                return redirect('assignments:panel')
                
            csv_file = request.FILES['csv_file']
            if not csv_file.name.endswith('.csv'):
                messages.error(request, 'El archivo debe tener extensión .csv')
                return redirect('assignments:panel')

            use_case = ImportAssignmentsUseCase(repo)
            creados = 0
            errores = []

            try:
                decoded_file = csv_file.read().decode('utf-8-sig').splitlines()
                reader = csv.DictReader(decoded_file, delimiter=';')
                
                if reader.fieldnames:
                    reader.fieldnames = [str(c).strip().lower() for c in reader.fieldnames if c]

                with transaction.atomic():
                    for idx, row in enumerate(reader, start=2):
                        try:
                            use_case.execute(row, 2026)
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
        'assignments': assignments
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