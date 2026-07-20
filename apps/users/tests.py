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