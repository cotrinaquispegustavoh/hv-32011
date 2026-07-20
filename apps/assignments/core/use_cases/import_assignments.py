from typing import Dict, Any, Tuple
from apps.users.infrastructure.models import User
from apps.academics.infrastructure.models import Section
from apps.assignments.core.domain.entities import TeacherAssignmentEntity
from apps.assignments.core.domain.repositories import ITeacherAssignmentRepository

class ImportAssignmentsUseCase:
    def __init__(self, assignment_repo: ITeacherAssignmentRepository):
        self.assignment_repo = assignment_repo

    def execute(self, row_data: Dict[str, Any], year: int) -> Tuple[bool, str]:
        """
        Espera un diccionario con: dni_docente, grado, letra, area
        """
        dni = str(row_data.get('dni_docente', '')).strip()
        grado = str(row_data.get('grado', '')).strip()
        letra = str(row_data.get('letra', '')).strip().upper()
        area = str(row_data.get('area', 'Polidocencia')).strip()

        if not dni or not grado or not letra:
            raise ValueError("Faltan datos obligatorios (DNI, Grado o Letra).")

        # 1. Buscar al Docente
        teacher = User.objects.filter(dni=dni, role='DOCENTE', is_active=True).first()
        if not teacher:
            raise ValueError(f"Docente con DNI {dni} no encontrado o inactivo.")

        # 2. Buscar la Sección
        section = Section.objects.filter(grade__iexact=grado, letter=letra, year=year).first()
        if not section:
            raise ValueError(f"Sección {grado} '{letra}' no encontrada en el año {year}.")

        # 3. Crear y guardar la asignación
        assignment = TeacherAssignmentEntity(
            id=None,
            teacher_id=teacher.id,
            section_id=section.id,
            area=area,
            academic_year=year
        )
        
        self.assignment_repo.save(assignment)
        return True, f"{teacher.last_name} -> {grado} {letra} ({area})"