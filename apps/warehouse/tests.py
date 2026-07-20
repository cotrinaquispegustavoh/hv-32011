from django.test import TestCase
from apps.warehouse.infrastructure.models import Material
from apps.warehouse.infrastructure.repositories.warehouse_repository import DjangoMaterialRepository, DjangoLoanRequestRepository
from apps.warehouse.core.use_cases.manage_loans import CreateLoanRequestUseCase
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