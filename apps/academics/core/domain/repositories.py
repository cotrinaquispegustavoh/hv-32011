from abc import ABC, abstractmethod
from typing import List, Optional
from .entities import SectionEntity, ParentEntity, StudentEntity

class ISectionRepository(ABC):
    @abstractmethod
    def get_all_by_year(self, year: int) -> List[SectionEntity]: pass
    
    @abstractmethod
    def get_by_grade_letter(self, grade: str, letter: str, year: int) -> Optional[SectionEntity]: pass

class IParentRepository(ABC):
    @abstractmethod
    def get_by_user_id(self, user_id: int) -> Optional[ParentEntity]: pass
    
    @abstractmethod
    def save(self, user_id: int) -> ParentEntity: pass

class IStudentRepository(ABC):
    @abstractmethod
    def get_by_parent(self, parent_id: int) -> List[StudentEntity]: pass
    @abstractmethod
    def get_by_section(self, section_id: int) -> List[StudentEntity]: pass
    @abstractmethod
    def get_all_students(self) -> List[StudentEntity]: pass
    
    @abstractmethod
    def save(self, student: StudentEntity) -> StudentEntity: pass