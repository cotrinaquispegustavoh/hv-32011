from dataclasses import dataclass
from typing import Optional

@dataclass
class TeacherAssignmentEntity:
    id: Optional[int]
    teacher_id: int
    section_id: int
    area: str
    academic_year: int