from typing import List
from apps.assignments.core.domain.entities import TeacherAssignmentEntity
from apps.assignments.core.domain.repositories import ITeacherAssignmentRepository
from apps.assignments.infrastructure.models import TeacherAssignment

class DjangoTeacherAssignmentRepository(ITeacherAssignmentRepository):
    
    def _to_entity(self, model: TeacherAssignment) -> TeacherAssignmentEntity:
        return TeacherAssignmentEntity(
            id=model.id,
            teacher_id=model.teacher_id,
            section_id=model.section_id,
            area=model.area,
            academic_year=model.academic_year
        )

    def get_by_teacher(self, teacher_id: int, year: int) -> List[TeacherAssignmentEntity]:
        models = TeacherAssignment.objects.filter(teacher_id=teacher_id, academic_year=year)
        return [self._to_entity(m) for m in models]

    def get_by_section(self, section_id: int, year: int) -> List[TeacherAssignmentEntity]:
        models = TeacherAssignment.objects.filter(section_id=section_id, academic_year=year)
        return [self._to_entity(m) for m in models]