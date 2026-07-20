from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime

@dataclass
class ObservationEntity:
    id: Optional[int]
    portfolio_item_id: int
    director_id: int
    content: str
    created_at: Optional[datetime] = None

@dataclass
class PortfolioItemEntity:
    id: Optional[int]
    teacher_id: int
    section_id: Optional[int]
    section_name: Optional[str]
    item_type: str
    title: str
    description: str
    file_path: str
    created_at: Optional[datetime] = None
    observations: List[ObservationEntity] = field(default_factory=list)
    teacher_name: Optional[str] = None # <-- NUEVO CAMPO