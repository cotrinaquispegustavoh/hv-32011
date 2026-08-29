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
