import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.http import JsonResponse
from django.shortcuts import redirect, render

from apps.academics.infrastructure.models import Student
from apps.core.core.use_cases.manage_notifications import NotifyAdminsUseCase, NotifyUserUseCase
from apps.core.infrastructure.repositories.core_repository import DjangoNotificationRepository
from apps.core.utils import normalize_text
from apps.discipline.core.use_cases.manage_incidents import (
    GetAllIncidentsUseCase,
    GetTeacherIncidentsUseCase,
    ReportIncidentUseCase,
)
from apps.discipline.infrastructure.models import Incident
from apps.discipline.infrastructure.repositories.discipline_repository import DjangoIncidentRepository
from apps.discipline.interfaces.forms import IncidentReportForm
from apps.discipline.student_access import accessible_sections, accessible_students
from apps.users.interfaces.middlewares import require_permission


logger = logging.getLogger(__name__)


def _student_payload(student):
    return {
        'id': student.pk,
        'name': f'{student.first_name} {student.last_name}'.strip(),
        'dni': student.dni or '',
        'section_id': student.section_id,
        'section': student.section.display_name,
        'grade': student.section.grade,
    }


def _selected_students(form, user):
    students = accessible_students(user)
    primary_id = form['student'].value()
    primary = students.filter(pk=primary_id).first() if primary_id else None
    additional_ids = form.data.getlist('additional_students') if form.is_bound else []
    additional = students.filter(pk__in=additional_ids)
    return (
        _student_payload(primary) if primary else None,
        [_student_payload(student) for student in additional],
    )


def _report_context(form, user):
    sections = list(accessible_sections(user))
    selected_student, selected_additional = _selected_students(form, user)
    return {
        'form': form,
        'is_teacher_scope': user.role == 'DOCENTE',
        'available_sections': sections,
        'available_grades': sorted({section.grade for section in sections}),
        'category_subtypes': {
            category: [
                {'value': value, 'label': label}
                for value, label in subtypes
            ]
            for category, subtypes in Incident.CATEGORY_SUBTYPES.items()
        },
        'selected_student': selected_student,
        'selected_additional_students': selected_additional,
    }


@login_required(login_url='/auth/login/')
@require_permission('discipline.create')
def report_incident_view(request):
    form = IncidentReportForm(
        request.POST or None,
        request.FILES or None,
        user=request.user,
    )
    if request.method == 'POST' and form.is_valid():
        data = form.cleaned_data
        student = data['student']
        evidence_path = None
        if data.get('evidence'):
            evidence_path = default_storage.save(
                f'discipline_evidences/{data["evidence"].name}',
                data['evidence'],
            )

        try:
            incident = ReportIncidentUseCase(DjangoIncidentRepository()).execute(
                student_id=student.pk,
                reported_by_id=request.user.pk,
                occurred_at=data['occurred_at'],
                location=data['location'],
                other_location=data['other_location'],
                category=data['category'],
                severity=data['severity'],
                subtype=data['subtype'],
                description=data['description'].strip(),
                additional_people=data['additional_people'].strip(),
                immediate_action=data['immediate_action'].strip(),
                requires_follow_up=data['requires_follow_up'],
                referred_to=data['referred_to'],
                additional_observations=data['additional_observations'].strip(),
                academic_year=student.section.year,
                additional_student_ids=list(
                    data['additional_students'].values_list('pk', flat=True)
                ),
                evidence_paths=[evidence_path] if evidence_path else [],
            )

        except Exception:
            if evidence_path:
                default_storage.delete(evidence_path)
            logger.exception('No se pudo registrar la incidencia.')
            messages.error(request, 'No se pudo registrar la incidencia. Inténtalo nuevamente.')
        else:
            try:
                notification_repo = DjangoNotificationRepository()
                student = Student.objects.select_related('parent__user').get(pk=student.pk)
                if student.parent and student.parent.user:
                    NotifyUserUseCase(notification_repo).execute(
                        user_id=student.parent.user.pk,
                        title='Nueva incidencia escolar',
                        message=(
                            f'Se registró la incidencia {incident.code} '
                            f'({incident.severity}) para {student.first_name}.'
                        ),
                        link=f'/academico/apoderado/hijo/{student.pk}/',
                    )

                if incident.severity == 'GRAVE':
                    NotifyAdminsUseCase(notification_repo).execute(
                        title='Incidencia grave registrada',
                        message=(
                            f'Se registró la incidencia grave {incident.code} '
                            f'para {student.first_name}.'
                        ),
                        link='/disciplina/historial/',
                    )

                async_to_sync(get_channel_layer().group_send)(
                    'directors_group',
                    {
                        'type': 'send_alert',
                        'alert_type': 'new_incident',
                        'message': f'Nueva incidencia {incident.severity} reportada.',
                        'severity': incident.severity,
                    },
                )
            except Exception:
                # El registro oficial ya existe; una caída temporal del canal de
                # avisos no debe duplicarlo ni eliminar su evidencia.
                logger.exception(
                    'La incidencia %s se guardó, pero falló una notificación.',
                    incident.code,
                )

            messages.success(request, f'Incidencia {incident.code} registrada correctamente.')
            return redirect('core:dashboard')

    return render(
        request,
        'discipline/report_incident.html',
        _report_context(form, request.user),
    )


@login_required(login_url='/auth/login/')
@require_permission('discipline.create')
def student_search_view(request):
    query = (request.GET.get('q') or '').strip()
    grade = (request.GET.get('grade') or '').strip()
    section_id = (request.GET.get('section_id') or '').strip()
    students = accessible_students(request.user)

    if grade:
        students = students.filter(section__grade=grade)
    if section_id:
        if not section_id.isdigit():
            return JsonResponse({'results': []})
        students = students.filter(section_id=section_id)

    if query:
        if len(query) < 2:
            return JsonResponse({'results': []})
        normalized_tokens = normalize_text(query).split()
        matches = []
        # Los nombres pueden contener tildes. Normalizar en Python conserva la
        # búsqueda "Perez" -> "Pérez" sin depender de extensiones de PostgreSQL.
        for student in students[:1000]:
            searchable = normalize_text(
                f'{student.first_name} {student.last_name} {student.dni or ""}'
            )
            if all(token in searchable for token in normalized_tokens):
                matches.append(student)
                if len(matches) == 20:
                    break
    elif request.user.role != 'DOCENTE' and not (grade or section_id):
        return JsonResponse({'results': []})
    else:
        matches = list(students[:20])

    return JsonResponse({
        'results': [_student_payload(student) for student in matches],
    })


@login_required(login_url='/auth/login/')
@require_permission('discipline.create')
def section_search_view(request):
    grade = (request.GET.get('grade') or '').strip()
    sections = accessible_sections(request.user)
    if grade:
        sections = sections.filter(grade=grade)
    return JsonResponse({
        'results': [
            {'id': section.pk, 'name': section.display_name, 'grade': section.grade}
            for section in sections
        ],
    })


@login_required(login_url='/auth/login/')
@require_permission('discipline.review')
def incident_list_view(request):
    repo = DjangoIncidentRepository()
    if request.user.role == 'DOCENTE':
        incidents = GetTeacherIncidentsUseCase(repo).execute(request.user.id)
    else:
        incidents = GetAllIncidentsUseCase(repo).execute()

    query = normalize_text(request.GET.get('q', ''))
    if query:
        incidents = [
            incident for incident in incidents
            if query in normalize_text(incident.student_name)
            or query in normalize_text(incident.description)
            or query in normalize_text(incident.code)
        ]
    return render(
        request,
        'discipline/incident_list.html',
        {'incidents': incidents, 'initial_query': request.GET.get('q', '')},
    )


@login_required(login_url='/auth/login/')
@require_permission('discipline.review')
def search_incidents_view(request):
    repo = DjangoIncidentRepository()
    if request.user.role == 'DOCENTE':
        incidents = GetTeacherIncidentsUseCase(repo).execute(request.user.id)
    else:
        incidents = GetAllIncidentsUseCase(repo).execute()

    query = normalize_text(request.GET.get('q', ''))
    severity = request.GET.get('severity', '')
    category = request.GET.get('category', '')
    if query:
        incidents = [
            incident for incident in incidents
            if query in normalize_text(incident.student_name)
            or query in normalize_text(incident.description)
            or query in normalize_text(incident.code)
        ]
    if severity:
        incidents = [incident for incident in incidents if incident.severity == severity]
    if category:
        incidents = [incident for incident in incidents if incident.category == category]
    return render(
        request,
        'discipline/partials/incident_table_rows.html',
        {'incidents': incidents},
    )
