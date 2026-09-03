from django.db.models import Q
from django.utils import timezone

from apps.core.infrastructure.models import InstitutionalAnnouncement, InternalNotification

def notifications_processor(request):
    if request.user.is_authenticated:
        # Contamos las no leídas
        unread_count = InternalNotification.objects.filter(user=request.user, is_read=False).count()
        # Traemos las 5 más recientes
        latest_notifs = InternalNotification.objects.filter(user=request.user).order_by('-created_at')[:5]
        
        context = {
            'unread_notifs_count': unread_count,
            'latest_notifs': latest_notifs
        }

        audience_by_role = {
            'DOCENTE': ['ALL', 'TEACHERS'],
            'APODERADO': ['ALL', 'PARENTS'],
        }
        audiences = audience_by_role.get(request.user.role)
        if audiences and request.resolver_match and request.resolver_match.url_name != 'announcement_detail':
            context['pending_announcement'] = (
                InstitutionalAnnouncement.objects
                .filter(is_active=True, audience__in=audiences)
                .filter(Q(valid_until__isnull=True) | Q(valid_until__gte=timezone.localdate()))
                .exclude(acknowledgements__user=request.user)
                .select_related('created_by')
                .first()
            )
        return context
    return {}
