from typing import List
from apps.assignments.core.domain.entities import TeacherAssignmentEntity
from apps.assignments.core.domain.repositories import ITeacherAssignmentRepository

class AssignTeacherUseCase:
    def __init__(self, assignment_repo: ITeacherAssignmentRepository):
        self.assignment_repo = assignment_repo

    def execute(self, teacher_id: int, section_ids: List[int], area: str, year: int) -> List[TeacherAssignmentEntity]:
        assignments = []
        for section_id in section_ids:
            assignment = TeacherAssignmentEntity(
                id=None,
                teacher_id=teacher_id,
                section_id=section_id,
                area=area,
                academic_year=year
            )
            # Guardamos cada asignación
            assignments.append(self.assignment_repo.save(assignment))
        return assignments

class RemoveAssignmentUseCase:
    def __init__(self, assignment_repo: ITeacherAssignmentRepository):
        self.assignment_repo = assignment_repo

    def execute(self, assignment_id: int) -> bool:
        return self.assignment_repo.delete(assignment_id)