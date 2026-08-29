from django.test import Client, TestCase
from django.urls import reverse

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
