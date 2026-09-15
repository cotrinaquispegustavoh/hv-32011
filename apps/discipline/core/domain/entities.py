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
    occurred_at: datetime
    location: str
    other_location: str
    category: str
    severity: str
    subtype: str
    description: str
    additional_people: str
    immediate_action: str
    requires_follow_up: bool
    referred_to: str
    additional_observations: str
    academic_year: int
    additional_student_ids: List[int] = field(default_factory=list)
    date_reported: Optional[datetime] = None
    evidences: List[EvidenceEntity] = field(default_factory=list)
    code: Optional[str] = None
    status: str = 'REGISTRADA'
    student_name: Optional[str] = None
    section_name: Optional[str] = None
    reporter_name: Optional[str] = None
    category_label: Optional[str] = None
    subtype_label: Optional[str] = None
    location_label: Optional[str] = None
    status_label: Optional[str] = None
    referred_to_label: Optional[str] = None
    additional_student_names: List[str] = field(default_factory=list)
