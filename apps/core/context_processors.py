from apps.core.infrastructure.models import InternalNotification

def notifications_processor(request):
    if request.user.is_authenticated:
        # Contamos las no leídas
        unread_count = InternalNotification.objects.filter(user=request.user, is_read=False).count()
        # Traemos las 5 más recientes
        latest_notifs = InternalNotification.objects.filter(user=request.user).order_by('-created_at')[:5]
        
        return {
            'unread_notifs_count': unread_count,
            'latest_notifs': latest_notifs
        }
    return {}