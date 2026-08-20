from typing import List, Tuple
from datetime import datetime
from django.utils import timezone
from apps.warehouse.core.domain.entities import LoanRequestEntity, LoanDetailEntity
from apps.warehouse.core.domain.repositories import IMaterialRepository, ILoanRequestRepository

class CreateLoanRequestUseCase:
    def __init__(self, material_repo: IMaterialRepository, loan_repo: ILoanRequestRepository):
        self.material_repo = material_repo
        self.loan_repo = loan_repo

    def execute(self, teacher_id: int, items: List[Tuple[int, int]], required_for: str, expected_return_date: str) -> LoanRequestEntity:
        
        # --- CORRECCIÓN: Manejo estricto de Zonas Horarias ---
        try:
            # 1. Parseamos el texto que viene del HTML
            dt_pickup_naive = datetime.fromisoformat(required_for)
            dt_return_naive = datetime.fromisoformat(expected_return_date)
            
            # 2. Le inyectamos la zona horaria oficial del sistema (America/Lima)
            dt_pickup = timezone.make_aware(dt_pickup_naive)
            dt_return = timezone.make_aware(dt_return_naive)
            
            # 3. Comparamos con la hora exacta actual del servidor
            if dt_return <= dt_pickup:
                raise ValueError("La fecha de retorno debe ser posterior a la fecha de recojo.")
            if dt_pickup < timezone.now():
                raise ValueError("No puedes programar un recojo en el pasado.")
        except ValueError as e:
            if "posterior" in str(e) or "pasado" in str(e): 
                raise e
            raise ValueError("Formato de fecha inválido.")

        details = []
        for material_id, quantity in items:
            material = self.material_repo.get_by_id(material_id)
            if not material: 
                raise ValueError(f"El material con ID {material_id} no existe.")
            if material.stock < quantity: 
                raise ValueError(f"Stock insuficiente. Solo quedan {material.stock} unidades de '{material.name}'.")
            
            new_stock = material.stock - quantity
            self.material_repo.update_stock(material_id, new_stock)
            
            details.append(LoanDetailEntity(
                id=None, material_id=material_id, quantity_requested=quantity,
                quantity_returned=0, quantity_waste=0
            ))
        
        loan_request = LoanRequestEntity(
            id=None, teacher_id=teacher_id, request_date=None,
            required_for=dt_pickup, expected_return_date=dt_return, # Guardamos las fechas con zona horaria
            status='PENDING', details=details
        )
        return self.loan_repo.save(loan_request)

class UpdateLoanStatusUseCase:
    def __init__(self, material_repo: IMaterialRepository, loan_repo: ILoanRequestRepository):
        self.material_repo = material_repo
        self.loan_repo = loan_repo

    def execute(self, loan_id: int, new_status: str) -> LoanRequestEntity:
        loan = self.loan_repo.get_by_id(loan_id)
        if not loan:
            raise ValueError("La solicitud no existe.")

        if new_status in ['RETURNED', 'CANCELLED'] and loan.status not in ['RETURNED', 'CANCELLED']:
            for detail in loan.details:
                material = self.material_repo.get_by_id(detail.material_id)
                if material:
                    if new_status == 'RETURNED':
                        detail.quantity_returned = detail.quantity_requested
                    
                    new_stock = material.stock + detail.quantity_requested
                    self.material_repo.update_stock(material.id, new_stock)

        loan.status = new_status
        return self.loan_repo.save(loan)

class GetTeacherLoansUseCase:
    def __init__(self, loan_repo: ILoanRequestRepository):
        self.loan_repo = loan_repo

    def execute(self, teacher_id: int) -> List[LoanRequestEntity]:
        return self.loan_repo.get_by_teacher(teacher_id)