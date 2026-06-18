from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime

@dataclass
class EvidenceEntity:
    id: Optional[int]
    incident_id: int
    file_path: str

@dataclass
class IncidentEntity:
    id: Optional[int]
    student_id: int
    reported_by_id: int
    severity: str
    subtype: str
    description: str
    date_reported: Optional[datetime] = None
    evidences: List[EvidenceEntity] = field(default_factory=list)
    student_name: Optional[str] = None
    reporter_name: Optional[str] = None