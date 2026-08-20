from typing import List, Optional
from django.db import transaction
from apps.warehouse.core.domain.entities import MaterialEntity, LoanRequestEntity, LoanDetailEntity
from apps.warehouse.core.domain.repositories import IMaterialRepository, ILoanRequestRepository
from apps.warehouse.infrastructure.models import Material, MaterialImage, LoanRequest, LoanDetail

class DjangoMaterialRepository(IMaterialRepository):
    def get_all(self) -> List[MaterialEntity]:
        return [self._to_entity(m) for m in Material.objects.all().order_by('name')]

    def get_by_id(self, material_id: int) -> Optional[MaterialEntity]:
        try:
            return self._to_entity(Material.objects.get(id=material_id))
        except Material.DoesNotExist:
            return None

    def update_stock(self, material_id: int, new_stock: int) -> bool:
        return Material.objects.filter(id=material_id).update(stock=new_stock) > 0

    def get_by_name(self, name: str) -> Optional[MaterialEntity]:
        try:
            return self._to_entity(Material.objects.get(name__iexact=name))
        except Material.DoesNotExist:
            return None

    @transaction.atomic
    def save(self, material: MaterialEntity) -> MaterialEntity:
        model, _ = Material.objects.update_or_create(
            id=material.id,
            defaults={
                'name': material.name,
                'category': material.category,
                'stock': material.stock,
                'unit': material.unit,
                'state': material.state,
                'location': material.location,
                'cycle': material.cycle,
                'pedagogical_use': material.pedagogical_use
            }
        )
        
        # Si se subió una nueva imagen, borramos la anterior y guardamos la nueva
        if material.new_image_path:
            MaterialImage.objects.filter(material=model, is_main=True).delete()
            MaterialImage.objects.create(material=model, image=material.new_image_path, is_main=True)
            
        return self._to_entity(model)

    def delete(self, material_id: int) -> bool:
        try:
            material = Material.objects.get(id=material_id)
            material.delete()
            return True
        except Material.DoesNotExist:
            return False

    def _to_entity(self, model: Material) -> MaterialEntity:
        # Buscamos la imagen principal
        main_img = model.images.filter(is_main=True).first()
        img_url = main_img.image.name if main_img and main_img.image else None
        
        return MaterialEntity(
            id=model.id, name=model.name, category=model.category, stock=model.stock, unit=model.unit,
            state=model.state, location=model.location, cycle=model.cycle,
            pedagogical_use=model.pedagogical_use, main_image_url=img_url
        )

class DjangoLoanRequestRepository(ILoanRequestRepository):
    @transaction.atomic
    def save(self, request: LoanRequestEntity) -> LoanRequestEntity:
        model, _ = LoanRequest.objects.update_or_create(
            id=request.id,
            defaults={
                'teacher_id': request.teacher_id, 
                'status': request.status,
                'required_for': request.required_for,
                'expected_return_date': request.expected_return_date
            }
        )
        request.id = model.id
        request.request_date = model.request_date

        for detail in request.details:
            LoanDetail.objects.update_or_create(
                id=detail.id,
                loan_request=model,
                defaults={
                    'material_id': detail.material_id,
                    'quantity_requested': detail.quantity_requested,
                    'quantity_returned': detail.quantity_returned,
                    'quantity_waste': detail.quantity_waste
                }
            )
        return request

    def _to_entity(self, model: LoanRequest) -> LoanRequestEntity:
        details = [LoanDetailEntity(
            id=d.id, material_id=d.material_id, quantity_requested=d.quantity_requested,
            quantity_returned=d.quantity_returned, quantity_waste=d.quantity_waste,
            material_name=d.material.name, material_unit=d.material.unit
        ) for d in model.details.all()]
        
        teacher_name = f"{model.teacher.first_name} {model.teacher.last_name}"
        
        return LoanRequestEntity(
            id=model.id, teacher_id=model.teacher_id, request_date=model.request_date,
            status=model.status, required_for=model.required_for, 
            expected_return_date=model.expected_return_date, details=details,
            teacher_name=teacher_name
        )

    def get_by_teacher(self, teacher_id: int) -> List[LoanRequestEntity]:
        models = LoanRequest.objects.filter(teacher_id=teacher_id).prefetch_related('details__material', 'teacher').order_by('-request_date')
        return [self._to_entity(m) for m in models]

    def get_all_active(self) -> List[LoanRequestEntity]:
        models = LoanRequest.objects.exclude(status__in=['RETURNED', 'CANCELLED']).prefetch_related('details__material', 'teacher').order_by('required_for')
        return [self._to_entity(m) for m in models]

    def get_by_id(self, loan_id: int) -> Optional[LoanRequestEntity]:
        try:
            model = LoanRequest.objects.prefetch_related('details__material', 'teacher').get(id=loan_id)
            return self._to_entity(model)
        except LoanRequest.DoesNotExist:
            return None