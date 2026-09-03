from typing import List, Optional
from apps.academics.core.domain.entities import SectionEntity, ParentEntity, StudentEntity
from apps.academics.core.domain.repositories import ISectionRepository, IParentRepository, IStudentRepository
from apps.academics.infrastructure.models import Section, Parent, Student

class DjangoSectionRepository(ISectionRepository):
    def get_all_by_year(self, year: int) -> List[SectionEntity]:
        models = Section.objects.filter(year=year)
        return [SectionEntity(id=m.id, grade=m.grade, letter=m.letter, name=m.name, year=m.year) for m in models]

    def get_by_grade_letter(self, grade: str, letter: str, year: int) -> Optional[SectionEntity]:
        try:
            m = Section.objects.get(grade__iexact=grade, letter__iexact=letter, year=year)
            return SectionEntity(id=m.id, grade=m.grade, letter=m.letter, name=m.name, year=m.year)
        except Section.DoesNotExist:
            return None

    def get_by_grade_name(self, grade: str, name: str, year: int) -> Optional[SectionEntity]:
        try:
            m = Section.objects.get(grade__iexact=grade, name__iexact=name, year=year)
            return SectionEntity(id=m.id, grade=m.grade, letter=m.letter, name=m.name, year=m.year)
        except Section.DoesNotExist:
            return None

class DjangoParentRepository(IParentRepository):
    def get_by_user_id(self, user_id: int) -> Optional[ParentEntity]:
        try:
            model = Parent.objects.get(user_id=user_id)
            return ParentEntity(id=model.id, user_id=model.user_id)
        except Parent.DoesNotExist:
            return None

    def save(self, user_id: int) -> ParentEntity:
        model, _ = Parent.objects.get_or_create(user_id=user_id)
        return ParentEntity(id=model.id, user_id=model.user_id)

class DjangoStudentRepository(IStudentRepository):
    def _to_entity(self, model: Student) -> StudentEntity:
        tutor_name = "Sin tutor asignado"
        if hasattr(model, 'section') and model.section:
            if hasattr(model.section, 'assignments'):
                for assign in model.section.assignments.all():
                    if 'Polidocencia' in assign.area:
                        tutor_name = f"{assign.teacher.first_name} {assign.teacher.last_name}"
                        break

        return StudentEntity(
            id=model.id,
            dni=model.dni or "Sin DNI",
            first_name=model.first_name,
            last_name=model.last_name,
            parent_id=model.parent_id,
            section_id=model.section_id,
            section_name=model.section.display_name if model.section else "Sin sección",
            parent_name=f"{model.parent.user.first_name} {model.parent.user.last_name}" if model.parent else "Sin apoderado",
            parent_phone=model.parent.user.phone if model.parent and hasattr(model.parent.user, 'phone') and model.parent.user.phone else "No registrado",
            tutor_name=tutor_name
        )

    def get_by_parent(self, parent_id: int) -> List[StudentEntity]:
        models = Student.objects.filter(parent_id=parent_id).select_related('section', 'parent__user').prefetch_related('section__assignments__teacher')
        return [self._to_entity(m) for m in models]

    def get_by_section(self, section_id: int) -> List[StudentEntity]:
        models = Student.objects.filter(section_id=section_id).select_related('section', 'parent__user').prefetch_related('section__assignments__teacher')
        return [self._to_entity(m) for m in models]

    def get_all_students(self) -> List[StudentEntity]:
        models = Student.objects.all().select_related('section', 'parent__user').prefetch_related('section__assignments__teacher').order_by('section__grade', 'section__name', 'last_name')
        return [self._to_entity(m) for m in models]

    def save(self, student: StudentEntity) -> StudentEntity:
        model, _ = Student.objects.update_or_create(
            dni=student.dni,
            defaults={
                'first_name': student.first_name,
                'last_name': student.last_name,
                'parent_id': student.parent_id,
                'section_id': student.section_id
            }
        )
        return self._to_entity(model)
