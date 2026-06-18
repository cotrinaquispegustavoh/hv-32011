from typing import Optional, List
from apps.users.core.domain.entities import UserEntity
from apps.users.core.domain.repositories import IUserRepository
from apps.users.infrastructure.models import User as UserModel

class DjangoUserRepository(IUserRepository):
    def _to_entity(self, model: UserModel) -> UserEntity:
        return UserEntity(
            id=model.id, dni=model.dni, role=model.role,
            first_name=model.first_name, last_name=model.last_name,
            password_changed=model.password_changed, is_active=model.is_active,
            support_role=model.support_role, module_permissions=model.module_permissions
        )

    def get_by_dni(self, dni: str) -> Optional[UserEntity]:
        try:
            return self._to_entity(UserModel.objects.get(dni=dni))
        except UserModel.DoesNotExist:
            return None

    def save(self, user: UserEntity) -> UserEntity:
        model, _ = UserModel.objects.update_or_create(
            dni=user.dni,
            defaults={
                'role': user.role, 'first_name': user.first_name, 'last_name': user.last_name,
                'password_changed': user.password_changed, 'is_active': user.is_active,
                'support_role': user.support_role, 'module_permissions': user.module_permissions
            }
        )
        return self._to_entity(model)

    def get_all_staff(self) -> List[UserEntity]:
        models = UserModel.objects.exclude(role='APODERADO').order_by('role', 'last_name')
        return [self._to_entity(m) for m in models]

    def toggle_active_status(self, user_id: int, current_user_id: int) -> bool:
        try:
            user = UserModel.objects.get(id=user_id)
            # REGLAS DE SEGURIDAD
            if user.id == current_user_id:
                raise ValueError("No puedes suspender tu propia cuenta.")
            if user.role == 'SUPERUSER':
                raise ValueError("No se puede suspender al Superuser Técnico.")
                
            user.is_active = not user.is_active
            user.save()
            return user.is_active
        except UserModel.DoesNotExist:
            raise ValueError("Usuario no encontrado.")

    def bulk_update_permissions(self, user_ids: List[int], modules: List[str]) -> bool:
        # Actualiza los permisos de todos los IDs seleccionados en una sola consulta
        UserModel.objects.filter(id__in=user_ids).update(module_permissions=modules)
        return True