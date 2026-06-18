from typing import List, Optional
from apps.academics.core.domain.entities import SectionEntity, ParentEntity, StudentEntity
from apps.academics.core.domain.repositories import ISectionRepository, IParentRepository, IStudentRepository
from apps.academics.infrastructure.models import Section, Parent, Student

class DjangoSectionRepository(ISectionRepository):
    def get_all_by_year(self, year: int) -> List[SectionEntity]:
        models = Section.objects.filter(year=year)
        return [SectionEntity(id=m.id, grade=m.grade, letter=m.letter, name=m.name, year=m.year) for m in models]

class DjangoParentRepository(IParentRepository):
    def get_by_user_id(self, user_id: int) -> Optional[ParentEntity]:
        try:
            model = Parent.objects.get(user_id=user_id)
            return ParentEntity(id=model.id, user_id=model.user_id)
        except Parent.DoesNotExist:
            return None

class DjangoStudentRepository(IStudentRepository):
    def get_by_parent(self, parent_id: int) -> List[StudentEntity]:
        models = Student.objects.filter(parent_id=parent_id)
        return [StudentEntity(id=m.id, first_name=m.first_name, last_name=m.last_name, 
                              parent_id=m.parent_id, section_id=m.section_id) for m in models]

    def get_by_section(self, section_id: int) -> List[StudentEntity]:
        models = Student.objects.filter(section_id=section_id)
        return [StudentEntity(id=m.id, first_name=m.first_name, last_name=m.last_name, 
                              parent_id=m.parent_id, section_id=m.section_id) for m in models]