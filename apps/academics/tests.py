from django.test import Client, TestCase
from django.urls import reverse

from apps.academics.core.use_cases.import_students import ImportStudentsUseCase
from apps.academics.infrastructure.models import Section, Student
from apps.academics.infrastructure.repositories.academics_repository import (
    DjangoParentRepository,
    DjangoSectionRepository,
    DjangoStudentRepository,
)
from apps.users.infrastructure.repositories.user_repository import DjangoUserRepository
from apps.users.infrastructure.models import User


class StudentImportPermissionTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_teacher_can_view_directory_but_cannot_import_students(self):
        teacher = User.objects.create_user(
            dni='41234567',
            role='DOCENTE',
            password_changed=True,
        )
        self.client.force_login(teacher)

        view_response = self.client.get(reverse('academics:student_directory'))
        import_response = self.client.post(
            reverse('academics:student_directory'),
            {'action': 'csv_upload'},
        )

        self.assertEqual(view_response.status_code, 200)
        self.assertNotContains(view_response, 'Importar Matrícula')
        self.assertEqual(import_response.status_code, 403)

    def test_director_keeps_access_to_student_import(self):
        director = User.objects.create_user(
            dni='11234567',
            role='DIRECTOR',
            password_changed=True,
        )
        self.client.force_login(director)

        response = self.client.get(reverse('academics:student_directory'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Importar Matrícula')


class NamedSectionTests(TestCase):
    def setUp(self):
        self.section = Section.objects.create(
            grade='1°', letter='-', name='Huánuco', year=2026
        )
        self.use_case = ImportStudentsUseCase(
            DjangoUserRepository(),
            DjangoSectionRepository(),
            DjangoParentRepository(),
            DjangoStudentRepository(),
        )

    def test_section_display_uses_grade_and_place_name(self):
        self.assertEqual(self.section.display_name, '1° - Huánuco')
        self.assertEqual(str(self.section), '1° - Huánuco (2026)')

    def test_student_import_uses_named_section(self):
        self.use_case.execute(
            {
                'dni_apoderado': '70123456',
                'nombres_apoderado': 'María',
                'apellidos_apoderado': 'López',
                'dni_alumno': '80123456',
                'nombres_alumno': 'Ana',
                'apellidos_alumno': 'López',
                'grado': '1°',
                'seccion': 'Huánuco',
            },
            2026,
        )

        student = Student.objects.get(dni='80123456')
        self.assertEqual(student.section, self.section)

    def test_legacy_letter_column_remains_compatible(self):
        legacy_section = Section.objects.create(
            grade='2°', letter='B', name='Amarilis', year=2026
        )

        self.use_case.execute(
            {
                'dni_apoderado': '70123457',
                'nombres_apoderado': 'Luis',
                'apellidos_apoderado': 'Ramos',
                'dni_alumno': '80123457',
                'nombres_alumno': 'Pedro',
                'apellidos_alumno': 'Ramos',
                'grado': '2°',
                'letra': 'B',
            },
            2026,
        )

        self.assertEqual(Student.objects.get(dni='80123457').section, legacy_section)
