from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from PIL import Image

from apps.warehouse.infrastructure.models import Material, MaterialImage, LoanRequest
from apps.warehouse.infrastructure.repositories.warehouse_repository import DjangoMaterialRepository, DjangoLoanRequestRepository
from apps.warehouse.core.use_cases.manage_loans import CreateLoanRequestUseCase, UpdateLoanStatusUseCase
from apps.users.infrastructure.models import User
from datetime import datetime, timedelta

class WarehouseLogicTests(TestCase):
    def setUp(self):
        # Preparamos el entorno de prueba creando un usuario y un material temporal
        self.teacher = User.objects.create_user(dni='44444444', role='DOCENTE', first_name='Test', last_name='Teacher')
        self.material = Material.objects.create(
            name='Proyector Epson', stock=5, unit='Unidades', 
            state='OPERATIVO', location='Almacén', cycle='TODOS'
        )
        self.material_repo = DjangoMaterialRepository()
        self.loan_repo = DjangoLoanRequestRepository()
        self.use_case = CreateLoanRequestUseCase(self.material_repo, self.loan_repo)
        self.client = Client()

    def test_soft_delete_material(self):
        """Prueba que al eliminar un material, no se borre de la BD, solo se oculte."""
        # 1. Ejecutamos el borrado
        self.material.delete()
        
        # 2. Verificamos que desaparece de la consulta normal (Catálogo)
        self.assertEqual(Material.objects.count(), 0)
        
        # 3. Verificamos que sigue en la base de datos con is_deleted=True (Papelera)
        deleted_material = Material.all_objects.first()
        self.assertIsNotNone(deleted_material)
        self.assertTrue(deleted_material.is_deleted)

    def test_prevent_negative_stock(self):
        """Prueba que el sistema bloquee un pedido mayor al stock disponible."""
        future_pickup = (datetime.now() + timedelta(days=1)).isoformat()
        future_return = (datetime.now() + timedelta(days=2)).isoformat()
        
        # Intentamos pedir 6 proyectores cuando solo hay 5
        with self.assertRaises(ValueError) as context:
            self.use_case.execute(
                teacher_id=self.teacher.id,
                items=[(self.material.id, 6)], # Pedimos 6
                required_for=future_pickup,
                expected_return_date=future_return
            )
        
        # Verificamos que el error exacto sea el de stock insuficiente
        self.assertIn("Stock insuficiente", str(context.exception))

    def test_rejects_zero_and_negative_quantities_without_changing_stock(self):
        future_pickup = (datetime.now() + timedelta(days=1)).isoformat()
        future_return = (datetime.now() + timedelta(days=2)).isoformat()

        for invalid_quantity in (0, -1):
            with self.subTest(quantity=invalid_quantity):
                with self.assertRaisesMessage(ValueError, "mayor que cero"):
                    self.use_case.execute(
                        teacher_id=self.teacher.id,
                        items=[(self.material.id, invalid_quantity)],
                        required_for=future_pickup,
                        expected_return_date=future_return,
                    )

        self.material.refresh_from_db()
        self.assertEqual(self.material.stock, 5)
        self.assertEqual(LoanRequest.objects.count(), 0)

    def test_valid_request_decrements_stock_and_creates_loan(self):
        future_pickup = (datetime.now() + timedelta(days=1)).isoformat()
        future_return = (datetime.now() + timedelta(days=2)).isoformat()

        loan = self.use_case.execute(
            teacher_id=self.teacher.id,
            items=[(self.material.id, 2)],
            required_for=future_pickup,
            expected_return_date=future_return,
        )

        self.material.refresh_from_db()
        self.assertEqual(self.material.stock, 3)
        self.assertEqual(loan.status, 'PENDING')

    def test_invalid_status_transition_does_not_change_loan_or_stock(self):
        future_pickup = (datetime.now() + timedelta(days=1)).isoformat()
        future_return = (datetime.now() + timedelta(days=2)).isoformat()
        loan = self.use_case.execute(
            teacher_id=self.teacher.id,
            items=[(self.material.id, 1)],
            required_for=future_pickup,
            expected_return_date=future_return,
        )

        status_use_case = UpdateLoanStatusUseCase(self.material_repo, self.loan_repo)
        with self.assertRaisesMessage(ValueError, "Cambio de estado no permitido"):
            status_use_case.execute(loan.id, 'RETURNED')

        self.material.refresh_from_db()
        saved_loan = LoanRequest.objects.get(id=loan.id)
        self.assertEqual(self.material.stock, 4)
        self.assertEqual(saved_loan.status, 'PENDING')

    def test_normal_dispatch_and_return_flow_restores_stock_only_once(self):
        future_pickup = (datetime.now() + timedelta(days=1)).isoformat()
        future_return = (datetime.now() + timedelta(days=2)).isoformat()
        loan = self.use_case.execute(
            teacher_id=self.teacher.id,
            items=[(self.material.id, 1)],
            required_for=future_pickup,
            expected_return_date=future_return,
        )
        status_use_case = UpdateLoanStatusUseCase(self.material_repo, self.loan_repo)

        status_use_case.execute(loan.id, 'DISPATCHED')
        status_use_case.execute(loan.id, 'RETURNED')
        status_use_case.execute(loan.id, 'RETURNED')

        self.material.refresh_from_db()
        saved_loan = LoanRequest.objects.get(id=loan.id)
        detail = saved_loan.details.get()
        self.assertEqual(self.material.stock, 5)
        self.assertEqual(saved_loan.status, 'RETURNED')
        self.assertEqual(detail.quantity_returned, 1)

    def test_non_numeric_quantity_returns_controlled_error(self):
        self.teacher.password_changed = True
        self.teacher.module_permissions = ['almacen']
        self.teacher.save(update_fields=['password_changed', 'module_permissions'])
        self.client.force_login(self.teacher)

        response = self.client.post(
            reverse('warehouse:request_material', args=[self.material.id]),
            {'quantity': 'no-es-un-numero'},
        )

        self.assertEqual(response.status_code, 400)
        self.assertContains(response, 'Cantidad inválida', status_code=400)
        self.material.refresh_from_db()
        self.assertEqual(self.material.stock, 5)

    def test_teacher_warehouse_opens_catalog_with_history_and_request_actions(self):
        self.teacher.password_changed = True
        self.teacher.module_permissions = ['almacen']
        self.teacher.save(update_fields=['password_changed', 'module_permissions'])
        self.client.force_login(self.teacher)

        response = self.client.get(reverse('warehouse:catalog'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Historial')
        self.assertContains(response, 'SOLICITAR')

    def test_teacher_loan_history_displays_domain_entity_status(self):
        self.teacher.password_changed = True
        self.teacher.module_permissions = ['almacen']
        self.teacher.save(update_fields=['password_changed', 'module_permissions'])
        self.client.force_login(self.teacher)
        self.use_case.execute(
            teacher_id=self.teacher.id,
            items=[(self.material.id, 1)],
            required_for=(datetime.now() + timedelta(days=1)).isoformat(),
            expected_return_date=(datetime.now() + timedelta(days=2)).isoformat(),
        )

        response = self.client.get(reverse('warehouse:loan_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Pendiente')
        self.assertContains(response, 'ui-table--responsive')

    def test_director_catalog_is_read_only_and_links_to_inventory(self):
        director = User.objects.create_user(
            dni='11111111', role='DIRECTOR', password_changed=True
        )
        self.client.force_login(director)

        response = self.client.get(reverse('warehouse:catalog'))
        forbidden_request = self.client.post(
            reverse('warehouse:request_material', args=[self.material.id]),
            {
                'quantity': '1',
                'required_for': (datetime.now() + timedelta(days=1)).isoformat(),
                'expected_return_date': (datetime.now() + timedelta(days=2)).isoformat(),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Gestionar inventario')
        self.assertNotContains(response, '>SOLICITAR<', html=False)
        self.assertEqual(forbidden_request.status_code, 403)
        self.material.refresh_from_db()
        self.assertEqual(self.material.stock, 5)

    def test_inventory_table_links_to_visual_catalog(self):
        director = User.objects.create_user(
            dni='11111112', role='DIRECTOR', password_changed=True
        )
        self.client.force_login(director)

        response = self.client.get(reverse('warehouse:inventory_panel'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Vista catálogo')
        self.assertContains(response, 'name="images"')
        self.assertContains(response, 'multiple')
        self.assertContains(response, 'capture="environment"')
        self.assertContains(response, 'max-height: 90dvh')

    def test_edit_material_displays_invalid_image_error_on_same_view(self):
        director = User.objects.create_user(
            dni='11111113', role='DIRECTOR', password_changed=True
        )
        self.client.force_login(director)
        invalid_image = SimpleUploadedFile(
            'material.gif', b'GIF89a', content_type='image/gif'
        )

        response = self.client.post(
            reverse('warehouse:edit_material', args=[self.material.pk]),
            {
                'name': self.material.name,
                'category': self.material.category,
                'stock': self.material.stock,
                'unit': self.material.unit,
                'state': self.material.state,
                'location': self.material.location,
                'cycle': self.material.cycle,
                'pedagogical_use': '',
                'image': invalid_image,
            },
            follow=True,
        )

        self.assertRedirects(
            response,
            reverse('warehouse:edit_material', args=[self.material.pk]),
        )
        self.assertContains(response, 'Formato no permitido')
        self.assertContains(response, 'WEBP')

    def test_edit_material_accepts_a_real_webp_image(self):
        director = User.objects.create_user(
            dni='11111114', role='DIRECTOR', password_changed=True
        )
        self.client.force_login(director)
        content = BytesIO()
        Image.new('RGB', (8, 8), 'white').save(content, format='WEBP')
        webp_image = SimpleUploadedFile(
            'material.webp', content.getvalue(), content_type='image/webp'
        )

        with TemporaryDirectory() as temporary_media, self.settings(MEDIA_ROOT=temporary_media):
            response = self.client.post(
                reverse('warehouse:edit_material', args=[self.material.pk]),
                {
                    'name': self.material.name,
                    'category': self.material.category,
                    'stock': self.material.stock,
                    'unit': self.material.unit,
                    'state': self.material.state,
                    'location': self.material.location,
                    'cycle': self.material.cycle,
                    'pedagogical_use': '',
                    'image': webp_image,
                },
            )

            self.assertRedirects(response, reverse('warehouse:inventory_panel'))
            saved_image = MaterialImage.objects.get(material=self.material, is_main=True)
            self.assertTrue(saved_image.image.name.endswith('.webp'))

    def test_edit_material_adds_multiple_images_and_mobile_capture(self):
        director = User.objects.create_user(
            dni='11111115', role='DIRECTOR', password_changed=True
        )
        self.client.force_login(director)

        def webp_upload(name, color):
            content = BytesIO()
            Image.new('RGB', (8, 8), color).save(content, format='WEBP')
            return SimpleUploadedFile(name, content.getvalue(), content_type='image/webp')

        with TemporaryDirectory() as temporary_media, self.settings(MEDIA_ROOT=temporary_media):
            response = self.client.post(
                reverse('warehouse:edit_material', args=[self.material.pk]),
                {
                    'name': self.material.name,
                    'category': self.material.category,
                    'stock': self.material.stock,
                    'unit': self.material.unit,
                    'state': self.material.state,
                    'location': self.material.location,
                    'cycle': self.material.cycle,
                    'pedagogical_use': '',
                    'images': [
                        webp_upload('frente.webp', 'white'),
                        webp_upload('lateral.webp', 'blue'),
                    ],
                    'camera_image': webp_upload('camara.webp', 'red'),
                },
            )

            self.assertRedirects(response, reverse('warehouse:inventory_panel'))
            self.assertEqual(MaterialImage.objects.filter(material=self.material).count(), 3)
            self.assertEqual(
                MaterialImage.objects.filter(material=self.material, is_main=True).count(),
                1,
            )

            catalog = self.client.get(reverse('warehouse:catalog'))
            self.assertContains(catalog, 'Ver imagen siguiente')
            self.assertContains(catalog, 'object-fill')

            primary_image = MaterialImage.objects.get(material=self.material, is_main=True)
            primary_path = Path(primary_image.image.path)
            self.assertTrue(primary_path.exists())
            with self.captureOnCommitCallbacks(execute=True):
                deletion = self.client.post(
                    reverse('warehouse:edit_material', args=[self.material.pk]),
                    {'delete_image_id': primary_image.pk},
                )

            self.assertRedirects(
                deletion,
                reverse('warehouse:edit_material', args=[self.material.pk]),
            )
            self.assertFalse(MaterialImage.objects.filter(pk=primary_image.pk).exists())
            self.assertFalse(primary_path.exists())
            self.assertEqual(MaterialImage.objects.filter(material=self.material).count(), 2)
            self.assertEqual(
                MaterialImage.objects.filter(material=self.material, is_main=True).count(),
                1,
            )
