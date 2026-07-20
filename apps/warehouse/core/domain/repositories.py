from abc import ABC, abstractmethod
from typing import List, Optional
from .entities import MaterialEntity, LoanRequestEntity

class IMaterialRepository(ABC):
    @abstractmethod
    def get_all(self) -> List[MaterialEntity]: pass

    @abstractmethod
    def get_by_id(self, material_id: int) -> Optional[MaterialEntity]: pass

    @abstractmethod
    def update_stock(self, material_id: int, new_stock: int) -> bool: pass

    @abstractmethod
    def get_by_name(self, name: str) -> Optional[MaterialEntity]: pass

    @abstractmethod
    def save(self, material: MaterialEntity) -> MaterialEntity: pass

    # --- NUEVA FUNCIÓN ---
    @abstractmethod
    def delete(self, material_id: int) -> bool: pass

class ILoanRequestRepository(ABC):
    @abstractmethod
    def save(self, request: LoanRequestEntity) -> LoanRequestEntity: pass

    @abstractmethod
    def get_by_teacher(self, teacher_id: int) -> List[LoanRequestEntity]: pass

    @abstractmethod
    def get_all_active(self) -> List[LoanRequestEntity]: pass

    @abstractmethod
    def get_by_id(self, loan_id: int) -> Optional[LoanRequestEntity]: pass