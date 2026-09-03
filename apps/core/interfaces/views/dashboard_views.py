from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from apps.core.core.use_cases.manage_dashboards import GetDirectorMetricsUseCase, GetTeacherMetricsUseCase
from apps.core.infrastructure.repositories.core_repository import DjangoNotificationRepository
from apps.core.core.use_cases.manage_notifications import MarkNotificationsReadUseCase
from apps.core.infrastructure.models import (
    AuditLog,
    InstitutionalAnnouncement,
    InternalNotification,
)
from apps.core.calendar_services import get_upcoming_calendar_items


MODEL_NAMES_ES = {
    'AnnouncementAcknowledgement': 'Constancia de lectura',
    'AuditLog': 'Registro de auditoría',
    'DocumentCategory': 'Categoría documental',
    'DocumentVersion': 'Versión documental',
    'Evidence': 'Evidencia de incidencia',
    'Incident': 'Incidencia',
    'InstitutionalDocument': 'Documento institucional',
    'InstitutionalAnnouncement': 'Comunicado institucional',
    'LoanRequest': 'Solicitud de material',
    'LoanDetail': 'Detalle de solicitud',
    'Material': 'Material',
    'MaterialImage': 'Imagen de material',
    'Migration': 'Migración del sistema',
    'Observation': 'Observación académica',
    'Parent': 'Apoderado',
    'PortfolioItem': 'Ficha académica',
    'Section': 'Aula',
    'Student': 'Estudiante',
    'TeacherAssignment': 'Asignación docente',
    'User': 'Usuario',
    'InstitutionalEvent': 'Evento institucional',
}


def _safe_next_url(request, fallback_name):
    next_url = request.POST.get('next', '')
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url
    return fallback_name

@login_required(login_url='/auth/login/')
def dashboard_view(request):
    user = request.user
    
    if user.role == 'APODERADO':
        return redirect('academics:parent_dashboard')
        
    context = {
        'role': user.role,
        'name': user.first_name or 'Usuario',
        'upcoming_events': get_upcoming_calendar_items(user),
    }

    if user.role in ['DIRECTOR', 'SUBDIRECTOR', 'SUPERUSER']:
        use_case = GetDirectorMetricsUseCase()
        context['metrics'] = use_case.execute(user.id)
        
    # --- NUEVO: Cargar métricas si es Docente ---
    elif user.role == 'DOCENTE':
        use_case = GetTeacherMetricsUseCase()
        context['metrics'] = use_case.execute(user.id)

    return render(request, 'core/dashboard.html', context)

@login_required(login_url='/auth/login/')
def mark_notifications_read_view(request):
    if request.method == 'POST':
        repo = DjangoNotificationRepository()
        MarkNotificationsReadUseCase(repo).execute(request.user.id)
        if request.headers.get('HX-Request') == 'true':
            response = HttpResponse('')
            response['HX-Trigger'] = 'notificationsUpdated'
            response['HX-Refresh'] = 'true'
            return response
        messages.success(request, 'Todas las notificaciones fueron marcadas como leídas.')
        return redirect(_safe_next_url(request, 'core:notifications'))
    return HttpResponseForbidden()

@login_required(login_url='/auth/login/')
def read_notification_view(request, notif_id):
    """Marca una notificación individual como leída y redirige a su enlace."""
    try:
        notif = InternalNotification.objects.get(id=notif_id, user=request.user)
        announcement_prefix = '/comunicados/'
        if notif.link and notif.link.startswith(announcement_prefix):
            announcement_id = notif.link.removeprefix(announcement_prefix).strip('/')
            if (
                announcement_id.isdigit()
                and not InstitutionalAnnouncement.objects.filter(
                    pk=int(announcement_id),
                ).exists()
            ):
                notif.delete()
                messages.info(
                    request,
                    'El comunicado ya no está disponible y la notificación fue retirada.',
                )
                return redirect('core:notifications')
        notif.is_read = True
        notif.save(update_fields=['is_read'])
        
        if notif.link and url_has_allowed_host_and_scheme(
            notif.link,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            return redirect(notif.link)
    except InternalNotification.DoesNotExist:
        pass
        
    return redirect('core:dashboard')


@login_required(login_url='/auth/login/')
def notifications_view(request):
    state = request.GET.get('state', 'all')
    query = request.GET.get('q', '').strip()
    notifications = InternalNotification.objects.filter(user=request.user)
    total_count = notifications.count()
    unread_count = notifications.filter(is_read=False).count()

    if state == 'unread':
        notifications = notifications.filter(is_read=False)
    elif state == 'read':
        notifications = notifications.filter(is_read=True)
    else:
        state = 'all'

    if query:
        notifications = notifications.filter(
            Q(title__icontains=query) | Q(message__icontains=query)
        )

    paginator = Paginator(notifications, 12)
    page_obj = paginator.get_page(request.GET.get('page'))
    query_params = request.GET.copy()
    query_params.pop('page', None)

    return render(request, 'core/notifications.html', {
        'page_obj': page_obj,
        'state': state,
        'query': query,
        'total_count': total_count,
        'unread_count': unread_count,
        'read_count': total_count - unread_count,
        'query_suffix': query_params.urlencode(),
        'current_url': request.get_full_path(),
    })


@login_required(login_url='/auth/login/')
def update_notification_state_view(request, notif_id):
    if request.method != 'POST':
        return HttpResponseForbidden()

    try:
        notification = InternalNotification.objects.get(id=notif_id, user=request.user)
    except InternalNotification.DoesNotExist:
        messages.error(request, 'La notificación ya no está disponible.')
        return redirect('core:notifications')

    notification.is_read = request.POST.get('state') == 'read'
    notification.save(update_fields=['is_read'])
    return redirect(_safe_next_url(request, 'core:notifications'))


@login_required(login_url='/auth/login/')
def activity_view(request):
    can_view_all = request.user.is_superuser
    if not can_view_all:
        return HttpResponseForbidden(
            'La auditoría técnica solo está disponible para superusuarios.'
        )
    scope = 'all'
    action = request.GET.get('action', '')
    model_name = request.GET.get('model', '')
    query = request.GET.get('q', '').strip()

    logs = AuditLog.objects.select_related('user')
    available_models = list(
        logs.order_by().values_list('model_name', flat=True).distinct()
    )
    if action:
        logs = logs.filter(action=action)
    if model_name:
        logs = logs.filter(model_name=model_name)
    if query:
        logs = logs.filter(
            Q(user__first_name__icontains=query)
            | Q(user__last_name__icontains=query)
            | Q(user__dni__icontains=query)
            | Q(model_name__icontains=query)
            | Q(object_id__icontains=query)
        )

    paginator = Paginator(logs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))
    for log in page_obj.object_list:
        log.friendly_model_name = MODEL_NAMES_ES.get(log.model_name, log.model_name)
        log.summary = (log.changes or {}).get('info', '').replace(
            log.model_name,
            log.friendly_model_name,
        )

    query_params = request.GET.copy()
    query_params.pop('page', None)
    model_choices = [
        (name, MODEL_NAMES_ES.get(name, name)) for name in sorted(available_models)
    ]

    return render(request, 'core/activity.html', {
        'page_obj': page_obj,
        'can_view_all': can_view_all,
        'scope': scope,
        'action': action,
        'model_name': model_name,
        'query': query,
        'action_choices': AuditLog.ACTION_CHOICES,
        'model_choices': model_choices,
        'query_suffix': query_params.urlencode(),
    })
