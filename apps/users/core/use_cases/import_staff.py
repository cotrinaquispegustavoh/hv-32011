from typing import Dict, Any, Tuple
from apps.users.core.domain.entities import UserEntity
from apps.users.core.domain.repositories import IUserRepository

class ImportStaffUseCase:
    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo

    def execute(self, row_data: Dict[str, Any]) -> Tuple[bool, str]:
        dni = str(row_data.get('dni', '')).strip()
        nombres = str(row_data.get('nombres', '')).strip()
        apellidos = str(row_data.get('apellidos', '')).strip()
        rol = str(row_data.get('rol', 'DOCENTE')).strip().upper()
        cargo = str(row_data.get('cargo_especifico', '')).strip()

        if not dni or not nombres or not apellidos:
            raise ValueError("Faltan datos obligatorios (DNI, Nombres o Apellidos).")

        if len(dni) != 8 or not dni.isdigit():
            raise ValueError(f"El DNI '{dni}' no es válido.")

        # Validar roles permitidos
        roles_permitidos = ['DIRECTOR', 'SUBDIRECTOR', 'DOCENTE', 'APOYO']
        if rol not in roles_permitidos:
            rol = 'DOCENTE' # Por defecto si escriben mal el rol

        existing_user = self.user_repo.get_by_dni(dni)
        
        if existing_user:
            # Si ya existe, solo actualizamos sus datos (no tocamos su contraseña)
            existing_user.first_name = nombres
            existing_user.last_name = apellidos
            existing_user.role = rol
            existing_user.support_role = cargo if cargo else None
            self.user_repo.save(existing_user)
            return False, f"{apellidos}, {nombres}"
        else:
            # Si es nuevo, lo creamos
            new_user = UserEntity(
                id=None,
                dni=dni,
                role=rol,
                first_name=nombres,
                last_name=apellidos,
                password_changed=False,
                is_active=True,
                support_role=cargo if cargo else None,
                module_permissions=[]
            )
            saved_user = self.user_repo.save(new_user)
            # Le asignamos el DNI como contraseña inicial
            self.user_repo.set_password(saved_user.id, dni)
            return True, f"{apellidos}, {nombres}"