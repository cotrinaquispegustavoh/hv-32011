from django.test import TestCase, Client
from django.urls import reverse
from apps.users.infrastructure.models import User

class SecurityRoleTests(TestCase):
    def setUp(self):
        # Simulamos un navegador web
        self.client = Client()
        # Creamos dos usuarios con la contraseña ya cambiada para saltar el middleware de primer acceso
        self.docente = User.objects.create_user(dni='44444444', role='DOCENTE', password_changed=True)
        self.director = User.objects.create_user(dni='11111111', role='DIRECTOR', password_changed=True)

    def test_docente_cannot_access_dispatch_panel(self):
        """Prueba que un Docente sea bloqueado al intentar entrar al Panel de Despacho."""
        # Iniciamos sesión como docente
        self.client.force_login(self.docente)
        
        # Intentamos entrar a la URL de despacho
        response = self.client.get(reverse('warehouse:dispatch_panel'))
        
        # Verificamos que el sistema lo bloquee (403 Forbidden o 302 Redirect)
        self.assertIn(response.status_code, [302, 403])

    def test_director_can_access_dispatch_panel(self):
        """Prueba que un Director sí pueda entrar al Panel de Despacho."""
        # Iniciamos sesión como director
        self.client.force_login(self.director)
        
        # Intentamos entrar a la URL de despacho
        response = self.client.get(reverse('warehouse:dispatch_panel'))
        
        # Verificamos que la página cargue correctamente (200 OK)
        self.assertEqual(response.status_code, 200)

    def test_password_change_rejects_common_numeric_password(self):
        user = User.objects.create_user(
            dni='12345678', role='DOCENTE', password='initial-password', password_changed=False
        )
        self.client.force_login(user)

        response = self.client.post(reverse('users:password_change'), {
            'new_password': '12345678',
            'confirm_password': '12345678',
        })

        user.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertFalse(user.password_changed)
        self.assertTrue(user.check_password('initial-password'))

    def test_password_change_accepts_valid_password(self):
        user = User.objects.create_user(
            dni='87654321', role='DOCENTE', password='initial-password', password_changed=False
        )
        self.client.force_login(user)

        response = self.client.post(reverse('users:password_change'), {
            'new_password': 'ClaveSegura!2026',
            'confirm_password': 'ClaveSegura!2026',
        })

        user.refresh_from_db()
        self.assertRedirects(response, reverse('core:dashboard'))
        self.assertTrue(user.password_changed)
        self.assertTrue(user.check_password('ClaveSegura!2026'))

    def test_profile_updates_personal_data_but_not_identity_or_role(self):
        self.client.force_login(self.docente)

        response = self.client.post(reverse('users:profile'), {
            'first_name': 'Rosa',
            'last_name': 'Pérez',
            'email': 'rosa@example.edu.pe',
            'birth_date': '1990-05-20',
            'phone': '+51 987 654 321',
            'dni': '99999999',
            'role': 'DIRECTOR',
        })

        self.assertRedirects(response, reverse('users:profile'))
        self.docente.refresh_from_db()
        self.assertEqual(self.docente.first_name, 'Rosa')
        self.assertEqual(self.docente.last_name, 'Pérez')
        self.assertEqual(self.docente.email, 'rosa@example.edu.pe')
        self.assertEqual(self.docente.phone, '+51 987 654 321')
        self.assertEqual(self.docente.dni, '44444444')
        self.assertEqual(self.docente.role, 'DOCENTE')

    def test_profile_rejects_invalid_phone(self):
        self.client.force_login(self.docente)

        response = self.client.post(reverse('users:profile'), {
            'first_name': 'Rosa',
            'last_name': 'Pérez',
            'email': '',
            'birth_date': '',
            'phone': 'teléfono inválido',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ingresa un teléfono válido')
        self.docente.refresh_from_db()
        self.assertIsNone(self.docente.phone)

    def test_logout_redirects_to_public_landing_page(self):
        self.client.force_login(self.docente)

        response = self.client.get(reverse('users:logout'))

        self.assertRedirects(response, reverse('core:home'))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_staff_selector_replaces_previous_detail_with_loading_state(self):
        self.client.force_login(self.director)

        response = self.client.get(reverse('users:staff_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="staff-detail-content"')
        self.assertContains(response, 'Cargando usuario...')
        self.assertContains(response, 'hx-target="#staff-detail-content"')
        self.assertContains(response, 'hx-sync="#staff-detail-content:replace"')

    def test_account_security_changes_password_and_keeps_current_session(self):
        self.docente.set_password('ClaveAnterior!2026')
        self.docente.save(update_fields=['password'])
        self.client.force_login(self.docente)

        response = self.client.post(reverse('users:security'), {
            'old_password': 'ClaveAnterior!2026',
            'new_password1': 'NuevaClaveSegura!2026',
            'new_password2': 'NuevaClaveSegura!2026',
        })

        self.assertRedirects(response, reverse('users:security'))
        self.docente.refresh_from_db()
        self.assertTrue(self.docente.check_password('NuevaClaveSegura!2026'))
        self.assertEqual(
            str(self.client.session.get('_auth_user_id')),
            str(self.docente.pk),
        )
        self.assertEqual(self.client.get(reverse('users:security')).status_code, 200)

    def test_account_security_rejects_an_incorrect_current_password(self):
        self.docente.set_password('ClaveAnterior!2026')
        self.docente.save(update_fields=['password'])
        self.client.force_login(self.docente)

        response = self.client.post(reverse('users:security'), {
            'old_password': 'ClaveEquivocada!2026',
            'new_password1': 'NuevaClaveSegura!2026',
            'new_password2': 'NuevaClaveSegura!2026',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'contraseña antigua es incorrecta')
        self.docente.refresh_from_db()
        self.assertTrue(self.docente.check_password('ClaveAnterior!2026'))
