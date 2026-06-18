from abc import ABC, abstractmethod
from typing import List, Optional
from .entities import MaterialEntity, LoanRequestEntity

class IMaterialRepository(ABC):
    @abstractmethod
    def get_all(self) -> List[MaterialEntity]:
        pass

    @abstractmethod
    def get_by_id(self, material_id: int) -> Optional[MaterialEntity]:
        pass

    @abstractmethod
    def update_stock(self, material_id: int, new_stock: int) -> bool:
        pass

class ILoanRequestRepository(ABC):
    @abstractmethod
    def save(self, request: LoanRequestEntity) -> LoanRequestEntity:
        pass

    @abstractmethod
    def get_by_teacher(self, teacher_id: int) -> List[LoanRequestEntity]:
        pass

    @abstractmethod
    def get_all_active(self) -> List[LoanRequestEntity]:
        """Obtiene todos los pedidos pendientes o despachados."""
        pass

    @abstractmethod
    def get_by_id(self, loan_id: int) -> Optional[LoanRequestEntity]:
        pass