from abc import ABC, abstractmethod
from typing import List
from .entities import NotificationEntity, AuditLogEntity, EventEntity

class INotificationRepository(ABC):
    @abstractmethod
    def save(self, notification: NotificationEntity) -> NotificationEntity:
        pass
    @abstractmethod
    def get_unread_by_user(self, user_id: int) -> List[NotificationEntity]:
        pass
    @abstractmethod
    def mark_as_read(self, notification_id: int) -> bool:
        pass

class IAuditRepository(ABC):
    @abstractmethod
    def save(self, log: AuditLogEntity) -> AuditLogEntity:
        pass
    @abstractmethod
    def get_by_model(self, model_name: str) -> List[AuditLogEntity]:
        pass

# --- NUEVO CONTRATO ---
class IEventRepository(ABC):
    @abstractmethod
    def get_upcoming_events(self, limit: int = 5) -> List[EventEntity]:
        pass