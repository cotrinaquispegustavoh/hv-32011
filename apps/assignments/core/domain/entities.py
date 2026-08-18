from dataclasses import dataclass, field
from typing import Optional, List

@dataclass
class StudentSimpleEntity:
    id: int
    first_name: str
    last_name: str

@dataclass
class TeacherAssignmentEntity:
    id: Optional[int]
    teacher_id: int
    section_id: int
    area: str
    academic_year: int
    
    # --- NUEVOS CAMPOS PARA LA VISTA DEL DOCENTE ---
    section_full_name: Optional[str] = None
    students: List[StudentSimpleEntity] = field(default_factory=list)