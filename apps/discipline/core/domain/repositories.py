from abc import ABC, abstractmethod
from typing import List, Optional
from .entities import IncidentEntity

class IIncidentRepository(ABC):
    @abstractmethod
    def save(self, incident: IncidentEntity) -> IncidentEntity:
        pass

    @abstractmethod
    def get_by_student(self, student_id: int) -> List[IncidentEntity]:
        pass

    @abstractmethod
    def get_all(self) -> List[IncidentEntity]:
        """Obtiene todas las incidencias ordenadas por fecha (Para el Director)."""
        pass
    
    @abstractmethod
    def get_by_reporter(self, reporter_id: int) -> List[IncidentEntity]:
        """Obtiene las incidencias reportadas por un docente específico."""
        pass