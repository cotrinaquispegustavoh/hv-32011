from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from apps.academics.infrastructure.models import Section
from apps.assignments.infrastructure.models import TeacherAssignment
from apps.users.infrastructure.models import User


class AssignmentPanelResponsiveTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.director = User.objects.create_user(
            dni='11000000', role='DIRECTOR', password_changed=True
        )
        self.teacher = User.objects.create_user(
            dni='44000000',
            role='DOCENTE',
            first_name='Rosa',
            last_name='Docente',
            password_changed=True,
        )
        self.section = Section.objects.create(
            grade='1°', letter='-', name='ATASH', year=timezone.now().year
        )
        self.assignment = TeacherAssignment.objects.create(
            teacher=self.teacher,
            section=self.section,
            area='Polidocencia (Tutor/a)',
            academic_year=timezone.now().year,
        )
        self.client.force_login(self.director)

    def test_panel_prioritizes_assignments_and_uses_mobile_cards(self):
        response = self.client.get(reverse('assignments:panel'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Nueva asignación')
        self.assertContains(response, '1° - ATASH')
        self.assertContains(response, 'hidden lg:block')
        self.assertContains(response, 'lg:hidden divide-y')
        self.assertNotContains(response, 'overflow-x-auto')

    def test_htmx_removal_refreshes_both_responsive_views(self):
        response = self.client.post(
            reverse('assignments:remove', args=[self.assignment.id]),
            HTTP_HX_REQUEST='true',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['HX-Refresh'], 'true')
        self.assertFalse(TeacherAssignment.objects.filter(id=self.assignment.id).exists())
