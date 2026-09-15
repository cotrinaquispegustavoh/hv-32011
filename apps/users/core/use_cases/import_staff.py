import re
import unicodedata
from typing import Dict, Any, Tuple

from apps.users.core.domain.entities import UserEntity
from apps.users.core.domain.repositories import IUserRepository


NAME_CONNECTORS = {'de', 'del', 'la', 'las', 'los', 'y', 'e'}
POSITION_ACRONYMS = {'IP', 'CIST', 'TIC', 'APAFA'}
ROLE_ALIASES = {
    'director': 'DIRECTOR',
    'directora': 'DIRECTOR',
    'subdirector': 'SUBDIRECTOR',
    'subdirectora': 'SUBDIRECTOR',
    'sub director': 'SUBDIRECTOR',
    'sub directora': 'SUBDIRECTOR',
    'docente': 'DOCENTE',
    'profesor': 'DOCENTE',
    'profesora': 'DOCENTE',
    'apoyo': 'APOYO',
    'personal de apoyo': 'APOYO',
}


def _plain_text(value: str) -> str:
    normalized = unicodedata.normalize('NFKD', value)
    return ''.join(char for char in normalized if not unicodedata.combining(char))


def normalize_person_name(value: Any) -> str:
    """Normaliza nombres en español sin capitalizar conectores internos."""
    cleaned = re.sub(r'\s+', ' ', str(value or '').strip())
    if not cleaned:
        return ''

    words = []
    for word_index, word in enumerate(cleaned.lower().split(' ')):
        if word_index > 0 and word in NAME_CONNECTORS:
            words.append(word)
            continue

        # Conserva apóstrofes y guiones, capitalizando cada segmento del nombre.
        pieces = re.split(r"([-'])", word)
        words.append(''.join(
            piece[:1].upper() + piece[1:] if piece not in {'-', "'"} else piece
            for piece in pieces
        ))
    return ' '.join(words)


def normalize_staff_position(value: Any) -> str:
    cleaned = re.sub(r'\s+', ' ', str(value or '').strip())
    if cleaned.upper() in POSITION_ACRONYMS:
        return cleaned.upper()
    return normalize_person_name(cleaned)


def normalize_staff_role(value: Any) -> Tuple[str, str | None]:
    """Convierte variantes habituales del CSV al código de rol del sistema."""
    raw_role = re.sub(r'\s+', ' ', str(value or 'DOCENTE').strip())
    normalized_key = _plain_text(raw_role).lower()

    if normalized_key.startswith('docente '):
        specialty = raw_role[len('docente '):].strip()
        return 'DOCENTE', normalize_staff_position(specialty)

    role = ROLE_ALIASES.get(normalized_key)
    if role is None:
        raise ValueError(f"El rol '{raw_role}' no es válido.")
    return role, None


class ImportStaffUseCase:
    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo

    def execute(self, row_data: Dict[str, Any]) -> Tuple[bool, str]:
        dni = str(row_data.get('dni', '')).strip()
        if len(dni) == 7 and dni.isdigit():
            dni = dni.zfill(8)

        nombres = normalize_person_name(row_data.get('nombres', ''))
        apellidos = normalize_person_name(row_data.get('apellidos', ''))
        correo = str(row_data.get('correo', '')).strip().lower()
        rol, role_specialty = normalize_staff_role(row_data.get('rol', 'DOCENTE'))
        cargo = normalize_staff_position(row_data.get('cargo_especifico', ''))
        if not cargo and role_specialty:
            cargo = role_specialty

        if not dni or not nombres or not apellidos:
            raise ValueError("Faltan datos obligatorios (DNI, Nombres o Apellidos).")

        if len(dni) != 8 or not dni.isdigit():
            raise ValueError(f"El DNI '{dni}' no es válido.")

        # --- CORRECCIÓN: Permisos automáticos para Directivos ---
        default_permissions = []
        if rol in ['DIRECTOR', 'SUBDIRECTOR']:
            default_permissions = ['almacen', 'disciplina', 'portafolio']

        existing_user = self.user_repo.get_by_dni(dni)
        
        if existing_user:
            existing_user.first_name = nombres
            existing_user.last_name = apellidos
            existing_user.email = correo
            existing_user.role = rol
            existing_user.support_role = cargo if cargo else None
            # Si es directivo y no tenía permisos, se los damos
            if rol in ['DIRECTOR', 'SUBDIRECTOR'] and not existing_user.module_permissions:
                existing_user.module_permissions = default_permissions
            self.user_repo.save(existing_user)
            return False, f"{apellidos}, {nombres}"
        else:
            new_user = UserEntity(
                id=None, dni=dni, role=rol, first_name=nombres, last_name=apellidos,
                email=correo, password_changed=False, is_active=True,
                support_role=cargo if cargo else None, 
                module_permissions=default_permissions # Asignamos los permisos por defecto
            )
            saved_user = self.user_repo.save(new_user)
            self.user_repo.set_password(saved_user.id, dni)
            return True, f"{apellidos}, {nombres}"
