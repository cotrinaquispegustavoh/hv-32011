from abc import ABC, abstractmethod
from typing import Optional, List
from .entities import UserEntity

class IUserRepository(ABC):
    @abstractmethod
    def get_by_dni(self, dni: str) -> Optional[UserEntity]: pass
    
    @abstractmethod
    def get_by_id(self, user_id: int) -> Optional[UserEntity]: pass # <-- NUEVO

    @abstractmethod
    def save(self, user: UserEntity) -> UserEntity: pass
    
    @abstractmethod
    def get_all_staff(self) -> List[UserEntity]: pass
    
    @abstractmethod
    def toggle_active_status(self, user_id: int, current_user_id: int) -> bool: pass
    
    @abstractmethod
    def bulk_update_permissions(self, user_ids: List[int], modules: List[str]) -> bool: pass