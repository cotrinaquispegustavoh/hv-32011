from abc import ABC, abstractmethod
from typing import List
from .entities import TeacherAssignmentEntity

class ITeacherAssignmentRepository(ABC):
    @abstractmethod
    def get_by_teacher(self, teacher_id: int, year: int) -> List[TeacherAssignmentEntity]:
        """Obtiene todas las aulas y cursos asignados a un docente en un año."""
        pass

    @abstractmethod
    def get_by_section(self, section_id: int, year: int) -> List[TeacherAssignmentEntity]:
        """Obtiene todos los docentes asignados a un aula en un año."""
        pass
    
    @abstractmethod
    def save(self, assignment: TeacherAssignmentEntity) -> TeacherAssignmentEntity:
        pass
        
    @abstractmethod
    def delete(self, assignment_id: int) -> bool:
        pass