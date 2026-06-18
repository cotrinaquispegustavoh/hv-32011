from typing import List
from apps.users.core.domain.entities import UserEntity
from apps.users.core.domain.repositories import IUserRepository

class GetStaffListUseCase:
    def __init__(self, user_repo: IUserRepository): self.user_repo = user_repo
    def execute(self) -> List[UserEntity]: return self.user_repo.get_all_staff()

class ToggleUserStatusUseCase:
    def __init__(self, user_repo: IUserRepository): self.user_repo = user_repo
    def execute(self, user_id: int, current_user_id: int) -> bool:
        return self.user_repo.toggle_active_status(user_id, current_user_id)

class BulkUpdatePermissionsUseCase:
    def __init__(self, user_repo: IUserRepository): self.user_repo = user_repo
    def execute(self, user_ids: List[int], modules: List[str]) -> bool:
        if not user_ids: raise ValueError("No se seleccionaron usuarios.")
        return self.user_repo.bulk_update_permissions(user_ids, modules)