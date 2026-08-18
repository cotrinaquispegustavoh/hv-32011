from typing import List
from apps.academics.core.domain.entities import StudentEntity
from apps.academics.core.domain.repositories import IStudentRepository

class GetStudentDirectoryUseCase:
    def __init__(self, student_repo: IStudentRepository):
        self.student_repo = student_repo

    def execute(self) -> List[StudentEntity]:
        return self.student_repo.get_all_students()