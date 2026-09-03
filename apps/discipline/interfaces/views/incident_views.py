from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.files.storage import default_storage
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from apps.discipline.infrastructure.repositories.discipline_repository import DjangoIncidentRepository
from apps.discipline.core.use_cases.manage_incidents import ReportIncidentUseCase, GetAllIncidentsUseCase
from apps.academics.infrastructure.models import Student
from apps.users.interfaces.middlewares import require_module_permission
from apps.core.infrastructure.repositories.core_repository import DjangoNotificationRepository
from apps.core.core.use_cases.manage_notifications import NotifyAdminsUseCase, NotifyUserUseCase
from apps.core.utils import normalize_text
from apps.core.file_validation import UploadValidationError, validate_evidence_upload

@login_required(login_url='/auth/login/')
@require_module_permission('disciplina')
def report_incident_view(request):
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        severity = request.POST.get('severity')
        subtype = request.POST.get('subtype')
        description = request.POST.get('description')
        
        evidence_paths = []
        if 'evidence' in request.FILES:
            file = request.FILES['evidence']
            try:
                validate_evidence_upload(file)
            except UploadValidationError as e:
                messages.error(request, str(e))
                return redirect('discipline:report_incident')
            filename = default_storage.save(f'discipline_evidences/{file.name}', file)
            evidence_paths.append(filename)

        repo = DjangoIncidentRepository()
        use_case = ReportIncidentUseCase(repo)
        
        try:
            incident = use_case.execute(
                student_id=int(student_id),
                reported_by_id=request.user.id,
                severity=severity,
                subtype=subtype,
                description=description,
                evidence_paths=evidence_paths
            )
            
            notif_repo = DjangoNotificationRepository()

            # --- NOTIFICAR AL APODERADO ---
            student = Student.objects.select_related('parent__user').get(id=student_id)
            if student.parent and student.parent.user:
                NotifyUserUseCase(notif_repo).execute(
                    user_id=student.parent.user.id,
                    title="Nuevo Reporte de Conducta",
                    message=f"Se ha registrado una incidencia ({severity}) para {student.first_name}. Revisa el portal de familia.",
                    link=f"/academico/apoderado/hijo/{student.id}/"
                )

            # Notificar a Directivos (Solo si es GRAVE)
            if severity == 'GRAVE':
                NotifyAdminsUseCase(notif_repo).execute(
                    title="Incidencia Grave Registrada",
                    message=f"Se ha reportado una incidencia grave para {student.first_name}. Revisa el historial.",
                    link="/disciplina/historial/"
                )

            # WebSockets para Directivos
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                "directors_group",
                {
                    "type": "send_alert",
                    "alert_type": "new_incident",
                    "message": f"Nueva incidencia {severity} reportada.",
                    "severity": severity
                }
            )

            messages.success(request, 'Incidencia registrada y enviada a Dirección.')
            return redirect('core:dashboard')
        except Exception as e:
            messages.error(request, f'Error al registrar: {str(e)}')

    students = Student.objects.all().order_by('last_name')
    return render(request, 'discipline/report_incident.html', {'students': students})

@login_required(login_url='/auth/login/')
@require_module_permission('disciplina')
def incident_list_view(request):
    repo = DjangoIncidentRepository()
    
    if request.user.role in ['DIRECTOR', 'SUBDIRECTOR', 'SUPERUSER']:
        incidents = GetAllIncidentsUseCase(repo).execute()
    elif request.user.role == 'DOCENTE':
        from apps.discipline.core.use_cases.manage_incidents import GetTeacherIncidentsUseCase
        incidents = GetTeacherIncidentsUseCase(repo).execute(request.user.id)
    else:
        return redirect('core:dashboard')

    query = normalize_text(request.GET.get('q', ''))
    if query:
        incidents = [i for i in incidents if query in normalize_text(i.student_name) or query in normalize_text(i.description)]

    return render(request, 'discipline/incident_list.html', {'incidents': incidents, 'initial_query': request.GET.get('q', '')})

@login_required(login_url='/auth/login/')
@require_module_permission('disciplina')
def search_incidents_view(request):
    repo = DjangoIncidentRepository()
    if request.user.role in ['DIRECTOR', 'SUBDIRECTOR', 'SUPERUSER']:
        incidents = GetAllIncidentsUseCase(repo).execute()
    elif request.user.role == 'DOCENTE':
        from apps.discipline.core.use_cases.manage_incidents import GetTeacherIncidentsUseCase
        incidents = GetTeacherIncidentsUseCase(repo).execute(request.user.id)
    else:
        return HttpResponseForbidden()

    # Normalizamos
    query = normalize_text(request.GET.get('q', ''))
    severity = request.GET.get('severity', '')
    subtype = request.GET.get('subtype', '')

    if query:
        incidents = [i for i in incidents if query in normalize_text(i.student_name) or query in normalize_text(i.description)]
    if severity:
        incidents = [i for i in incidents if i.severity == severity]
    if subtype:
        incidents = [i for i in incidents if i.subtype == subtype]

    return render(request, 'discipline/partials/incident_table_rows.html', {'incidents': incidents})
