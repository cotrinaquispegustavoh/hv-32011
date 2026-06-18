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
    user_id: int  # Solo guardamos el ID para no acoplar toda la entidad User aquí

@dataclass
class StudentEntity:
    id: Optional[int]
    first_name: str
    last_name: str
    parent_id: int
    section_id: int