from abc import ABC, abstractmethod
from typing import List
from datetime import date
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
    @abstractmethod
    def mark_all_as_read(self, user_id: int) -> bool:
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
        
    # --- NUEVA FUNCIÓN ---
    @abstractmethod
    def get_events_in_range(self, start_date: date, end_date: date) -> List[EventEntity]:
        """Obtiene todos los eventos en un rango de fechas (Para el Calendario)."""
        pass