from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from apps.core.core.use_cases.manage_events import GetCalendarEventsUseCase
from apps.core.calendar_services import dated_announcements_for_range
from apps.core.core.use_cases.manage_notifications import NotifyUserUseCase
from apps.core.infrastructure.models import (
    AnnouncementAcknowledgement,
    InstitutionalAnnouncement,
    InstitutionalEvent,
    InternalNotification,
)
from apps.core.infrastructure.repositories.core_repository import (
    DjangoEventRepository,
    DjangoNotificationRepository,
)
from apps.core.interfaces.forms import (
    InstitutionalAnnouncementForm,
    InstitutionalEventForm,
)
from apps.core.realtime import broadcast_group_event
from apps.users.infrastructure.models import User


DIRECTOR_ROLES = ['DIRECTOR', 'SUPERUSER']


def _is_director(user):
    return user.is_superuser or user.role in DIRECTOR_ROLES


def _safe_return_url(request, fallback_name):
    next_url = request.POST.get('next', '')
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url
    return fallback_name


def _target_users(audience='ALL'):
    roles = {
        'TEACHERS': ['DOCENTE'],
        'PARENTS': ['APODERADO'],
        'ALL': ['DOCENTE', 'APODERADO'],
    }[audience]
    return User.objects.filter(role__in=roles, is_active=True).only('id')


def _notify_users(users, title, message, link):
    use_case = NotifyUserUseCase(DjangoNotificationRepository())
    for user in users.iterator():
        use_case.execute(
            user_id=user.id,
            title=title,
            message=message,
            link=link,
        )


def _announcement_notification_content(announcement):
    summary = announcement.message.strip()
    if len(summary) > 160:
        summary = f'{summary[:157]}...'
    return f'Nuevo comunicado: {announcement.title}'[:200], summary


def _event_notification_link(event):
    return f'/calendario/?event={event.pk}'


def _sync_announcement_notifications(announcement):
    detail_url = reverse('core:announcement_detail', args=[announcement.pk])
    title, summary = _announcement_notification_content(announcement)
    target_ids = list(_target_users(announcement.audience).values_list('pk', flat=True))
    linked = InternalNotification.objects.filter(link=detail_url)
    linked.exclude(user_id__in=target_ids).delete()
    linked.filter(user_id__in=target_ids).update(title=title, message=summary)
    existing_ids = set(linked.values_list('user_id', flat=True))
    missing_ids = [user_id for user_id in target_ids if user_id not in existing_ids]
    if missing_ids:
        _notify_users(
            User.objects.filter(pk__in=missing_ids),
            title=title,
            message=summary,
            link=detail_url,
        )
    AnnouncementAcknowledgement.objects.filter(
        announcement=announcement,
    ).exclude(user_id__in=target_ids).delete()


@login_required(login_url='/auth/login/')
def calendar_view(request):
    recent_announcements = []
    if _is_director(request.user):
        recent_announcements = InstitutionalAnnouncement.objects.annotate(
            acknowledgement_count=Count('acknowledgements')
        )[:5]
    return render(request, 'core/calendar.html', {
        'recent_announcements': recent_announcements,
    })


@login_required(login_url='/auth/login/')
def api_calendar_events(request):
    """API consumida por FullCalendar; conserva ISO para transporte."""
    start_str = request.GET.get('start')
    end_str = request.GET.get('end')

    try:
        if start_str and end_str:
            start_date = datetime.fromisoformat(start_str.replace('Z', '')).date()
            end_date = datetime.fromisoformat(end_str.replace('Z', '')).date()
        else:
            start_date = timezone.localdate()
            end_date = timezone.localdate()
    except ValueError:
        return JsonResponse({'error': 'Rango de fechas inválido.'}, status=400)

    events = GetCalendarEventsUseCase(DjangoEventRepository()).execute(
        start_date,
        end_date,
    )
    events_data = []
    for event in events:
        events_data.append({
            'id': event.id,
            'title': event.title,
            'start': event.event_date.isoformat(),
            'allDay': True,
            'backgroundColor': '#DC2626' if event.is_holiday else '#2563EB',
            'borderColor': '#DC2626' if event.is_holiday else '#2563EB',
            'extendedProps': {
                'description': event.description,
                'display_date': event.event_date.strftime('%d/%m/%Y'),
                'is_holiday': event.is_holiday,
                'edit_url': reverse('core:edit_event', args=[event.id]) if _is_director(request.user) else '',
                'delete_url': reverse('core:delete_event', args=[event.id]) if _is_director(request.user) else '',
            },
        })

    for announcement in dated_announcements_for_range(
        request.user,
        start_date,
        end_date,
    ):
        events_data.append({
            'id': f'announcement-{announcement.pk}',
            'title': announcement.title,
            'start': announcement.event_date.isoformat(),
            'allDay': True,
            'backgroundColor': '#7C3AED',
            'borderColor': '#7C3AED',
            'extendedProps': {
                'description': announcement.message,
                'display_date': announcement.event_date.strftime('%d/%m/%Y'),
                'is_holiday': False,
                'is_announcement': True,
                'detail_url': reverse(
                    'core:announcement_detail',
                    args=[announcement.pk],
                ),
                'edit_url': reverse('core:edit_announcement', args=[announcement.pk]) if _is_director(request.user) else '',
                'delete_url': reverse('core:delete_announcement', args=[announcement.pk]) if _is_director(request.user) else '',
            },
        })

    return JsonResponse(events_data, safe=False)


@login_required(login_url='/auth/login/')
def create_event_view(request):
    if not _is_director(request.user):
        return HttpResponseForbidden('Solo Dirección puede añadir fechas institucionales.')

    if request.method == 'POST':
        form = InstitutionalEventForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                event = form.save()
                display_date = event.event_date.strftime('%d/%m/%Y')
                _notify_users(
                    _target_users(),
                    title='Nueva fecha institucional',
                    message=f'{event.title} — {display_date}.',
                    link=_event_notification_link(event),
                )
            messages.success(request, 'La fecha fue añadida y notificada correctamente.')
            return redirect('core:calendar')
    else:
        form = InstitutionalEventForm()

    return render(request, 'core/event_form.html', {'form': form})


@login_required(login_url='/auth/login/')
def create_announcement_view(request):
    if not _is_director(request.user):
        return HttpResponseForbidden('Solo Dirección puede publicar comunicados.')

    if request.method == 'POST':
        form = InstitutionalAnnouncementForm(request.POST, request.FILES)
        if form.is_valid():
            with transaction.atomic():
                announcement = form.save(commit=False)
                announcement.created_by = request.user
                announcement.save()
                detail_url = reverse('core:announcement_detail', args=[announcement.pk])
                title, summary = _announcement_notification_content(announcement)
                _notify_users(
                    _target_users(announcement.audience),
                    title=title,
                    message=summary,
                    link=detail_url,
                )
            messages.success(request, 'El comunicado fue publicado y enviado a sus destinatarios.')
            return redirect('core:announcement_detail', announcement_id=announcement.pk)
    else:
        form = InstitutionalAnnouncementForm()

    return render(request, 'core/announcement_form.html', {'form': form})


@login_required(login_url='/auth/login/')
def edit_event_view(request, event_id):
    if not _is_director(request.user):
        return HttpResponseForbidden('Solo Dirección puede editar fechas institucionales.')
    event = get_object_or_404(InstitutionalEvent, pk=event_id)
    old_link = _event_notification_link(event)
    if request.method == 'POST':
        form = InstitutionalEventForm(request.POST, instance=event)
        if form.is_valid():
            event = form.save()
            display_date = event.event_date.strftime('%d/%m/%Y')
            InternalNotification.objects.filter(link=old_link).update(
                title='Fecha institucional actualizada',
                message=f'{event.title} — {display_date}.',
                link=_event_notification_link(event),
            )
            messages.success(request, 'La fecha institucional fue actualizada.')
            return redirect('core:calendar')
    else:
        form = InstitutionalEventForm(instance=event, initial={
            'event_kind': 'HOLIDAY' if event.is_holiday else 'ACTIVITY',
        })
    return render(request, 'core/event_form.html', {
        'form': form,
        'is_editing': True,
        'event': event,
    })


@login_required(login_url='/auth/login/')
def delete_event_view(request, event_id):
    if not _is_director(request.user):
        return HttpResponseForbidden('Solo Dirección puede eliminar fechas institucionales.')
    event = get_object_or_404(InstitutionalEvent, pk=event_id)
    if request.method == 'POST':
        InternalNotification.objects.filter(link=_event_notification_link(event)).delete()
        event.delete()
        messages.success(request, 'La fecha institucional fue eliminada.')
        return redirect('core:calendar')
    return render(request, 'core/confirm_delete.html', {
        'item_type': 'fecha institucional',
        'item_title': event.title,
        'form_action': reverse('core:delete_event', args=[event.pk]),
        'cancel_url': reverse('core:calendar'),
        'impact': 'También desaparecerá del calendario y de las agendas internas.',
    })


@login_required(login_url='/auth/login/')
def edit_announcement_view(request, announcement_id):
    if not _is_director(request.user):
        return HttpResponseForbidden('Solo Dirección puede editar comunicados.')
    announcement = get_object_or_404(InstitutionalAnnouncement, pk=announcement_id)
    if request.method == 'POST':
        form = InstitutionalAnnouncementForm(
            request.POST,
            request.FILES,
            instance=announcement,
        )
        if form.is_valid():
            with transaction.atomic():
                announcement = form.save()
                _sync_announcement_notifications(announcement)
            messages.success(request, 'El comunicado y sus notificaciones fueron actualizados.')
            return redirect('core:announcement_detail', announcement_id=announcement.pk)
    else:
        form = InstitutionalAnnouncementForm(instance=announcement)
    return render(request, 'core/announcement_form.html', {
        'form': form,
        'is_editing': True,
        'announcement': announcement,
    })


@login_required(login_url='/auth/login/')
def delete_announcement_view(request, announcement_id):
    if not _is_director(request.user):
        return HttpResponseForbidden('Solo Dirección puede eliminar comunicados.')
    announcement = get_object_or_404(InstitutionalAnnouncement, pk=announcement_id)
    if request.method == 'POST':
        announcement.delete()
        messages.success(request, 'El comunicado y sus notificaciones fueron eliminados.')
        return redirect('core:calendar')
    return render(request, 'core/confirm_delete.html', {
        'item_type': 'comunicado',
        'item_title': announcement.title,
        'form_action': reverse('core:delete_announcement', args=[announcement.pk]),
        'cancel_url': reverse('core:announcement_detail', args=[announcement.pk]),
        'impact': 'También se eliminarán sus constancias de lectura y notificaciones asociadas.',
    })


def _announcement_for_user(request, announcement_id):
    announcement = get_object_or_404(
        InstitutionalAnnouncement.objects.select_related('created_by'),
        pk=announcement_id,
    )
    if _is_director(request.user):
        return announcement
    if not announcement.is_visible_to(request.user):
        return None
    return announcement


@login_required(login_url='/auth/login/')
def announcement_detail_view(request, announcement_id):
    announcement = _announcement_for_user(request, announcement_id)
    if announcement is None:
        return HttpResponseForbidden('Este comunicado no está dirigido a tu cuenta.')
    acknowledged = AnnouncementAcknowledgement.objects.filter(
        announcement=announcement,
        user=request.user,
    ).exists()
    context = {
        'announcement': announcement,
        'acknowledged': acknowledged,
    }
    if _is_director(request.user):
        detail_url = f'/comunicados/{announcement.pk}/'
        recipients = User.objects.filter(
            notifications__link=detail_url,
        ).distinct().order_by('last_name', 'first_name')
        acknowledgements = list(
            announcement.acknowledgements.select_related('user')
            .order_by('-acknowledged_at')
        )
        acknowledged_user_ids = [item.user_id for item in acknowledgements]
        context['reader_report'] = {
            'recipient_count': recipients.count(),
            'acknowledgements': acknowledgements,
            'pending_recipients': recipients.exclude(pk__in=acknowledged_user_ids),
        }
    return render(request, 'core/announcement_detail.html', context)


@login_required(login_url='/auth/login/')
@require_POST
def acknowledge_announcement_view(request, announcement_id):
    announcement = _announcement_for_user(request, announcement_id)
    if announcement is None or _is_director(request.user):
        return HttpResponseForbidden('No puedes registrar esta lectura.')

    acknowledgement, created = AnnouncementAcknowledgement.objects.get_or_create(
        announcement=announcement,
        user=request.user,
    )
    detail_url = f'/comunicados/{announcement.pk}/'
    InternalNotification.objects.filter(
        user=request.user,
        link=detail_url,
        is_read=False,
    ).update(is_read=True)
    if created:
        detail_url = f'/comunicados/{announcement.pk}/'
        recipient_count = User.objects.filter(
            notifications__link=detail_url,
        ).distinct().count()
        confirmed_count = announcement.acknowledgements.count()
        broadcast_group_event('announcement_read_receipts', {
            'alert_type': 'announcement_acknowledged',
            'announcement_id': announcement.pk,
            'user_id': request.user.pk,
            'user_name': request.user.get_full_name() or request.user.dni,
            'user_dni': request.user.dni,
            'acknowledged_at': timezone.localtime(
                acknowledgement.acknowledged_at,
            ).strftime('%d/%m/%Y %H:%M'),
            'recipient_count': recipient_count,
            'confirmed_count': confirmed_count,
            'pending_count': max(recipient_count - confirmed_count, 0),
        })
    if request.POST.get('next'):
        return redirect(_safe_return_url(request, 'core:dashboard'))
    messages.success(request, 'Tu lectura del comunicado quedó registrada.')
    return redirect('core:announcement_detail', announcement_id=announcement.pk)


@login_required(login_url='/auth/login/')
@require_POST
def toggle_announcement_view(request, announcement_id):
    if not _is_director(request.user):
        return HttpResponseForbidden('Solo Dirección puede cambiar la publicación.')
    announcement = get_object_or_404(InstitutionalAnnouncement, pk=announcement_id)
    announcement.is_active = not announcement.is_active
    announcement.save(update_fields=['is_active', 'updated_at'])
    state = 'publicado nuevamente' if announcement.is_active else 'retirado de la primera plana'
    messages.success(request, f'El comunicado fue {state}.')
    return redirect('core:announcement_detail', announcement_id=announcement.pk)
