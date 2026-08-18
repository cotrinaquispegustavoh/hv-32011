from typing import List
from apps.assignments.core.domain.entities import TeacherAssignmentEntity, StudentSimpleEntity
from apps.assignments.core.domain.repositories import ITeacherAssignmentRepository
from apps.assignments.infrastructure.models import TeacherAssignment

class DjangoTeacherAssignmentRepository(ITeacherAssignmentRepository):
    
    def _to_entity(self, model: TeacherAssignment) -> TeacherAssignmentEntity:
        students = []
        section_name = ""
        
        # Si la consulta incluyó la sección y los alumnos, los mapeamos
        if hasattr(model, 'section') and model.section:
            section_name = f"{model.section.grade} '{model.section.letter}' - {model.section.name}"
            if hasattr(model.section, 'students'):
                for student in model.section.students.all().order_by('last_name'):
                    students.append(StudentSimpleEntity(
                        id=student.id, 
                        first_name=student.first_name, 
                        last_name=student.last_name
                    ))

        return TeacherAssignmentEntity(
            id=model.id,
            teacher_id=model.teacher_id,
            section_id=model.section_id,
            area=model.area,
            academic_year=model.academic_year,
            section_full_name=section_name,
            students=students
        )

    def get_by_teacher(self, teacher_id: int, year: int) -> List[TeacherAssignmentEntity]:
        # Optimizamos la consulta para traer la sección y sus alumnos de golpe
        models = TeacherAssignment.objects.filter(teacher_id=teacher_id, academic_year=year).select_related('section').prefetch_related('section__students')
        return [self._to_entity(m) for m in models]

    def get_by_section(self, section_id: int, year: int) -> List[TeacherAssignmentEntity]:
        models = TeacherAssignment.objects.filter(section_id=section_id, academic_year=year).select_related('section').prefetch_related('section__students')
        return [self._to_entity(m) for m in models]

    def save(self, assignment: TeacherAssignmentEntity) -> TeacherAssignmentEntity:
        model, _ = TeacherAssignment.objects.update_or_create(
            id=assignment.id,
            defaults={
                'teacher_id': assignment.teacher_id,
                'section_id': assignment.section_id,
                'area': assignment.area,
                'academic_year': assignment.academic_year
            }
        )
        return self._to_entity(model)

    def delete(self, assignment_id: int) -> bool:
        return TeacherAssignment.objects.filter(id=assignment_id).delete()[0] > 0