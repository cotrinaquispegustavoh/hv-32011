from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime, date

@dataclass
class NotificationEntity:
    id: Optional[int]
    user_id: int
    title: str
    message: str
    is_read: bool
    link: Optional[str] = None
    created_at: Optional[datetime] = None

@dataclass
class AuditLogEntity:
    id: Optional[int]
    user_id: Optional[int]
    action: str
    model_name: str
    object_id: str
    changes: Optional[Dict[str, Any]]
    ip_address: Optional[str]
    timestamp: Optional[datetime] = None

# --- NUEVA ENTIDAD ---
@dataclass
class EventEntity:
    id: Optional[int]
    title: str
    description: str
    event_date: date
    is_holiday: bool