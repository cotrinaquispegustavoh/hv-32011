from typing import Dict, Any, Tuple
from apps.users.infrastructure.models import User
from apps.academics.infrastructure.models import Section
from apps.assignments.core.domain.entities import TeacherAssignmentEntity
from apps.assignments.core.domain.repositories import ITeacherAssignmentRepository

class ImportAssignmentsUseCase:
    def __init__(self, assignment_repo: ITeacherAssignmentRepository):
        self.assignment_repo = assignment_repo

    def execute(self, row_data: Dict[str, Any], year: int) -> Tuple[bool, str]:
        # Buscamos 'dni_docente' o simplemente 'dni' por si el Excel varía
        dni = str(row_data.get('dni_docente', row_data.get('dni', ''))).strip()
        grado = str(row_data.get('grado', '')).strip()
        seccion_nombre = str(row_data.get('seccion', '')).strip()
        area = str(row_data.get('area', 'Polidocencia')).strip()

        if not dni or not grado or not seccion_nombre:
            raise ValueError("Faltan datos obligatorios (DNI, Grado o Sección).")

        # CORRECCIÓN: Manejo de docentes sin DNI
        if dni.upper() == 'SIN_DNI':
            raise ValueError(f"No se puede asignar el aula {grado} {seccion_nombre} porque el docente no tiene DNI registrado.")

        teacher = User.objects.filter(dni=dni, role='DOCENTE', is_active=True).first()
        if not teacher:
            raise ValueError(f"Docente con DNI {dni} no encontrado.")

        section = Section.objects.filter(grade__icontains=grado, name__icontains=seccion_nombre, year=year).first()
        if not section:
            raise ValueError(f"Sección {grado} '{seccion_nombre}' no encontrada en el año {year}.")

        assignment = TeacherAssignmentEntity(
            id=None, teacher_id=teacher.id, section_id=section.id,
            area=area, academic_year=year
        )
        
        self.assignment_repo.save(assignment)
        return True, f"{teacher.last_name} -> {grado} {seccion_nombre}"