from abc import ABC, abstractmethod
from typing import List, Optional
from .entities import PortfolioItemEntity, ObservationEntity

class IPortfolioRepository(ABC):
    @abstractmethod
    def save(self, item: PortfolioItemEntity) -> PortfolioItemEntity:
        pass

    @abstractmethod
    def get_by_teacher(self, teacher_id: int) -> List[PortfolioItemEntity]:
        """Para que el docente vea su propio portafolio."""
        pass

    @abstractmethod
    def get_all(self) -> List[PortfolioItemEntity]:
        """Para que el Director pueda revisar todo."""
        pass

class IObservationRepository(ABC):
    @abstractmethod
    def save(self, observation: ObservationEntity) -> ObservationEntity:
        pass