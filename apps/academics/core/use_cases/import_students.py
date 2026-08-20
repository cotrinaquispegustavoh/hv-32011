from typing import Dict, Any, Tuple
from apps.users.core.domain.entities import UserEntity
from apps.users.core.domain.repositories import IUserRepository
from apps.academics.core.domain.entities import StudentEntity
from apps.academics.core.domain.repositories import ISectionRepository, IParentRepository, IStudentRepository

class ImportStudentsUseCase:
    def __init__(self, user_repo: IUserRepository, section_repo: ISectionRepository, parent_repo: IParentRepository, student_repo: IStudentRepository):
        self.user_repo = user_repo
        self.section_repo = section_repo
        self.parent_repo = parent_repo
        self.student_repo = student_repo

    def execute(self, row_data: Dict[str, Any], year: int) -> Tuple[bool, str]:
        dni_apoderado = str(row_data.get('dni_apoderado', '')).strip()
        nombres_apoderado = str(row_data.get('nombres_apoderado', '')).strip()
        apellidos_apoderado = str(row_data.get('apellidos_apoderado', '')).strip()

        dni_alumno = str(row_data.get('dni_alumno', '')).strip()
        nombres_alumno = str(row_data.get('nombres_alumno', '')).strip()
        apellidos_alumno = str(row_data.get('apellidos_alumno', '')).strip()
        grado = str(row_data.get('grado', '')).strip()
        letra = str(row_data.get('letra', '')).strip().upper()

        if not dni_apoderado or not dni_alumno or not grado or not letra:
            raise ValueError("Faltan datos obligatorios (DNI Apoderado, DNI Alumno, Grado o Letra).")

        # 1. Gestionar Usuario Apoderado
        user_parent = self.user_repo.get_by_dni(dni_apoderado)
        if not user_parent:
            user_parent = UserEntity(
                id=None, dni=dni_apoderado, role='APODERADO',
                first_name=nombres_apoderado, last_name=apellidos_apoderado,
                password_changed=False, is_active=True
            )
            user_parent = self.user_repo.save(user_parent)
            self.user_repo.set_password(user_parent.id, dni_apoderado) # Contraseña = DNI

        # 2. Gestionar Perfil Parent
        parent = self.parent_repo.get_by_user_id(user_parent.id)
        if not parent:
            parent = self.parent_repo.save(user_parent.id)

        # 3. Buscar Sección
        section = self.section_repo.get_by_grade_letter(grado, letra, year)
        if not section:
            raise ValueError(f"Sección {grado} '{letra}' no encontrada en el año {year}.")

        # 4. Crear Alumno
        student = StudentEntity(
            id=None, dni=dni_alumno, first_name=nombres_alumno, last_name=apellidos_alumno,
            parent_id=parent.id, section_id=section.id
        )
        self.student_repo.save(student)

        return True, f"{apellidos_alumno}, {nombres_alumno}"