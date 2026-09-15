"""Ámbito de estudiantes disponible para registrar incidencias."""

from django.utils import timezone

from apps.academics.infrastructure.models import Section, Student
from apps.assignments.infrastructure.models import TeacherAssignment


def active_academic_year():
    """El proyecto aún no posee un modelo de año activo; usa el año local."""

    return timezone.localdate().year


def accessible_sections(user):
    year = active_academic_year()
    sections = Section.objects.filter(year=year)
    if user.role == 'DOCENTE':
        section_ids = TeacherAssignment.objects.filter(
            teacher=user,
            academic_year=year,
        ).values_list('section_id', flat=True)
        sections = sections.filter(pk__in=section_ids)
    return sections.order_by('grade', 'name').distinct()


def accessible_students(user):
    """Aplica en backend la misma restricción que muestra el buscador."""

    return Student.objects.filter(
        section__in=accessible_sections(user),
    ).select_related('section').order_by('last_name', 'first_name').distinct()
