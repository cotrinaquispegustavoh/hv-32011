from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from apps.discipline.infrastructure.repositories.discipline_repository import DjangoIncidentRepository
from apps.discipline.core.use_cases.manage_incidents import ReportIncidentUseCase, GetAllIncidentsUseCase
from apps.academics.infrastructure.models import Student
from apps.users.interfaces.middlewares import require_module_permission

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
            fs = FileSystemStorage(location='media/discipline_evidences/')
            filename = fs.save(file.name, file)
            evidence_paths.append(f'discipline_evidences/{filename}')

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
            
            # --- MAGIA EN TIEMPO REAL ---
            # Enviamos el chispazo al grupo de directores
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
            # ----------------------------

            messages.success(request, 'Incidencia registrada y enviada a Dirección.')
            return redirect('core:dashboard')
        except Exception as e:
            messages.error(request, f'Error al registrar: {str(e)}')

    students = Student.objects.all().order_by('last_name')
    return render(request, 'discipline/report_incident.html', {'students': students})

@login_required(login_url='/auth/login/')
def incident_list_view(request):
    if request.user.role not in ['DIRECTOR', 'SUBDIRECTOR', 'SUPERUSER']:
        return redirect('core:dashboard')

    repo = DjangoIncidentRepository()
    use_case = GetAllIncidentsUseCase(repo)
    incidents = use_case.execute()

    return render(request, 'discipline/incident_list.html', {'incidents': incidents})