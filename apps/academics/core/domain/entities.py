from dataclasses import dataclass
from typing import Optional, List

@dataclass
class SectionEntity:
    id: Optional[int]
    grade: str
    letter: str
    name: str
    year: int

@dataclass
class ParentEntity:
    id: Optional[int]
    user_id: int

@dataclass
class StudentEntity:
    id: Optional[int]
    first_name: str
    last_name: str
    parent_id: int
    section_id: int
    # --- NUEVOS CAMPOS PARA EL DIRECTORIO ---
    dni: str = ""
    section_name: str = ""
    parent_name: str = ""
    parent_phone: str = ""
    tutor_name: str = ""