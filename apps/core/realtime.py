import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction


logger = logging.getLogger(__name__)


def user_notification_group(user_id):
    return f'user_notifications_{user_id}'


def broadcast_group_event(group_name, event):
    """Emite un evento no persistente después de confirmar la transacción."""

    def send_after_commit():
        try:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                group_name,
                {'type': 'send_alert', **event},
            )
        except Exception:
            logger.exception('No se pudo emitir un evento al grupo %s.', group_name)

    transaction.on_commit(send_after_commit)


def broadcast_notification(notification):
    """Entrega una notificación persistida al canal privado de su destinatario."""

    broadcast_group_event(user_notification_group(notification.user_id), {
        'alert_type': 'notification',
        'notification_id': notification.pk,
        'title': notification.title,
        'message': notification.message,
        'link': notification.link or '',
    })
