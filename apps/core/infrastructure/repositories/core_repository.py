from typing import List
from django.utils import timezone
from apps.core.core.domain.entities import NotificationEntity, AuditLogEntity, EventEntity
from apps.core.core.domain.repositories import INotificationRepository, IAuditRepository, IEventRepository
from apps.core.infrastructure.models import InternalNotification, AuditLog, InstitutionalEvent

class DjangoNotificationRepository(INotificationRepository):
    def save(self, notification: NotificationEntity) -> NotificationEntity:
        model, _ = InternalNotification.objects.update_or_create(
            id=notification.id,
            defaults={
                'user_id': notification.user_id,
                'title': notification.title,
                'message': notification.message,
                'is_read': notification.is_read,
                'link': notification.link
            }
        )
        notification.id = model.id
        notification.created_at = model.created_at
        return notification

    def get_unread_by_user(self, user_id: int) -> List[NotificationEntity]:
        models = InternalNotification.objects.filter(user_id=user_id, is_read=False)
        return [
            NotificationEntity(
                id=m.id, user_id=m.user_id, title=m.title, 
                message=m.message, is_read=m.is_read, link=m.link, created_at=m.created_at
            ) for m in models
        ]

    def mark_as_read(self, notification_id: int) -> bool:
        return InternalNotification.objects.filter(id=notification_id).update(is_read=True) > 0

    # --- CORRECCIÓN: Esta es la función que exigía el contrato y faltaba ---
    def mark_all_as_read(self, user_id: int) -> bool:
        return InternalNotification.objects.filter(user_id=user_id, is_read=False).update(is_read=True) > 0

class DjangoAuditRepository(IAuditRepository):
    def save(self, log: AuditLogEntity) -> AuditLogEntity:
        model = AuditLog.objects.create(
            user_id=log.user_id, action=log.action, model_name=log.model_name,
            object_id=log.object_id, changes=log.changes, ip_address=log.ip_address
        )
        log.id = model.id
        log.timestamp = model.timestamp
        return log

    def get_by_model(self, model_name: str) -> List[AuditLogEntity]:
        models = AuditLog.objects.filter(model_name=model_name)
        return [
            AuditLogEntity(
                id=m.id, user_id=m.user_id, action=m.action, model_name=m.model_name,
                object_id=m.object_id, changes=m.changes, ip_address=m.ip_address, timestamp=m.timestamp
            ) for m in models
        ]
        
class DjangoEventRepository(IEventRepository):
    def get_upcoming_events(self, limit: int = 5) -> List[EventEntity]:
        today = timezone.now().date()
        models = InstitutionalEvent.objects.filter(event_date__gte=today).order_by('event_date')[:limit]
        return [
            EventEntity(
                id=m.id, title=m.title, description=m.description, 
                event_date=m.event_date, is_holiday=m.is_holiday
            ) for m in models
        ]