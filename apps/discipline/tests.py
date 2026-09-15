from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.academics.infrastructure.models import Parent, Section, Student
from apps.assignments.infrastructure.models import TeacherAssignment
from apps.discipline.infrastructure.models import Incident
from apps.users.infrastructure.models import User
from apps.users.permissions import GRANULAR_PERMISSIONS_MARKER


class IncidentRegistrationTests(TestCase):
    def setUp(self):
        self.year = timezone.localdate().year
        self.director = User.objects.create_user(
            dni='10101010', password='ClaveDirector!2026', role='DIRECTOR',
            password_changed=True,
        )
        self.teacher = User.objects.create_user(
            dni='20202020', password='ClaveDocente!2026', role='DOCENTE',
            password_changed=True,
            module_permissions=[GRANULAR_PERMISSIONS_MARKER, 'discipline.create'],
        )
        self.support = User.objects.create_user(
            dni='30303030', password='ClaveApoyo!2026', role='APOYO',
            password_changed=True,
            module_permissions=[GRANULAR_PERMISSIONS_MARKER, 'discipline.create'],
        )
        parent_user = User.objects.create_user(
            dni='40404040', password='ClaveFamilia!2026', role='APODERADO',
            password_changed=True,
        )
        self.parent = Parent.objects.create(user=parent_user)
        self.assigned_section = Section.objects.create(
            grade='4°', letter='-', name='Cunyaj', year=self.year,
        )
        self.other_section = Section.objects.create(
            grade='5°', letter='-', name='Atash', year=self.year,
        )
        self.assigned_student = Student.objects.create(
            dni='70000001', first_name='Juan', last_name='Pérez López',
            parent=self.parent, section=self.assigned_section,
        )
        self.other_student = Student.objects.create(
            dni='70000002', first_name='María', last_name='Ramos Vega',
            parent=self.parent, section=self.other_section,
        )
        TeacherAssignment.objects.create(
            teacher=self.teacher,
            section=self.assigned_section,
            area='Polidocencia',
            academic_year=self.year,
        )

    def valid_data(self, student=None, **overrides):
        data = {
            'student': (student or self.assigned_student).pk,
            'occurred_at': timezone.localtime().strftime('%Y-%m-%dT%H:%M'),
            'location': 'PATIO',
            'other_location': '',
            'category': 'AGRESION',
            'subtype': 'VERBAL',
            'severity': 'LEVE',
            'description': 'Se observó una discusión durante el recreo.',
            'additional_people': '',
            'immediate_action': 'Se dialogó con los estudiantes.',
            'requires_follow_up': 'false',
            'referred_to': '',
            'additional_observations': '',
        }
        data.update(overrides)
        return data

    def test_teacher_search_is_limited_to_assigned_sections(self):
        self.client.force_login(self.teacher)
        response = self.client.get(reverse('discipline:student_search'), {'q': 'a'})
        self.assertEqual(response.json()['results'], [])

        response = self.client.get(reverse('discipline:student_search'), {'q': 'Juan Per'})
        ids = [item['id'] for item in response.json()['results']]
        self.assertEqual(ids, [self.assigned_student.pk])

        response = self.client.get(reverse('discipline:student_search'), {'q': 'María'})
        self.assertEqual(response.json()['results'], [])

    def test_teacher_cannot_post_student_outside_authorized_scope(self):
        self.client.force_login(self.teacher)
        response = self.client.post(
            reverse('discipline:report_incident'),
            self.valid_data(student=self.other_student),
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Escoja una opción válida')
        self.assertFalse(Incident.objects.exists())

    def test_authorized_support_can_filter_or_search_all_students(self):
        self.client.force_login(self.support)
        filtered = self.client.get(
            reverse('discipline:student_search'),
            {'grade': '5°', 'section_id': self.other_section.pk},
        )
        self.assertEqual(
            [item['id'] for item in filtered.json()['results']],
            [self.other_student.pk],
        )
        searched = self.client.get(
            reverse('discipline:student_search'), {'q': '70000001'}
        )
        self.assertEqual(searched.json()['results'][0]['id'], self.assigned_student.pk)

    def test_director_can_search_without_grade_and_sections_follow_grade(self):
        self.client.force_login(self.director)
        response = self.client.get(
            reverse('discipline:student_search'), {'q': 'Juan Per'}
        )
        self.assertEqual(response.json()['results'][0]['id'], self.assigned_student.pk)

        response = self.client.get(
            reverse('discipline:section_search'), {'grade': '4°'}
        )
        self.assertEqual(
            [item['id'] for item in response.json()['results']],
            [self.assigned_section.pk],
        )

    def test_valid_incident_uses_authenticated_author_and_automatic_fields(self):
        self.client.force_login(self.teacher)
        response = self.client.post(
            reverse('discipline:report_incident'),
            self.valid_data(
                reported_by=self.director.pk,
                status='CERRADA',
                academic_year=1990,
                referred_to='DIRECCION',
            ),
        )
        self.assertRedirects(response, reverse('core:dashboard'))
        incident = Incident.objects.get()
        self.assertEqual(incident.reported_by, self.teacher)
        self.assertEqual(incident.status, 'REGISTRADA')
        self.assertEqual(incident.academic_year, self.year)
        self.assertEqual(incident.category, 'AGRESION')
        self.assertEqual(incident.subtype, 'VERBAL')
        self.assertEqual(incident.severity, 'LEVE')
        self.assertFalse(incident.requires_follow_up)
        self.assertEqual(incident.referred_to, '')
        self.assertEqual(incident.code, f'INC-{self.year}-{incident.pk:06d}')

    def test_invalid_subtype_for_category_is_rejected(self):
        self.client.force_login(self.teacher)
        response = self.client.post(
            reverse('discipline:report_incident'),
            self.valid_data(category='AGRESION', subtype='CIBERACOSO'),
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'no corresponde a la categoría')
        self.assertFalse(Incident.objects.exists())

    def test_follow_up_requires_referral_and_no_follow_up_clears_it(self):
        self.client.force_login(self.teacher)
        response = self.client.post(
            reverse('discipline:report_incident'),
            self.valid_data(requires_follow_up='true', referred_to=''),
        )
        self.assertContains(response, 'Selecciona el área')
        self.assertFalse(Incident.objects.exists())

        response = self.client.post(
            reverse('discipline:report_incident'),
            self.valid_data(requires_follow_up='true', referred_to='TUTOR'),
        )
        self.assertRedirects(response, reverse('core:dashboard'))
        self.assertEqual(Incident.objects.get().referred_to, 'TUTOR')

    def test_future_date_is_rejected(self):
        self.client.force_login(self.teacher)
        future = timezone.localtime() + timedelta(days=1)
        response = self.client.post(
            reverse('discipline:report_incident'),
            self.valid_data(occurred_at=future.strftime('%Y-%m-%dT%H:%M')),
        )
        self.assertContains(response, 'no puede estar en el futuro')
        self.assertFalse(Incident.objects.exists())

    def test_additional_students_are_distinct_from_primary(self):
        self.client.force_login(self.director)
        data = self.valid_data()
        data['additional_students'] = [self.other_student.pk]
        response = self.client.post(reverse('discipline:report_incident'), data)
        self.assertRedirects(response, reverse('core:dashboard'))
        self.assertEqual(
            list(Incident.objects.get().additional_students.all()),
            [self.other_student],
        )

    def test_codes_are_unique_without_using_a_count(self):
        self.client.force_login(self.director)
        self.client.post(reverse('discipline:report_incident'), self.valid_data())
        self.client.post(
            reverse('discipline:report_incident'),
            self.valid_data(student=self.other_student),
        )
        codes = list(Incident.objects.order_by('pk').values_list('code', flat=True))
        self.assertEqual(len(codes), len(set(codes)))
