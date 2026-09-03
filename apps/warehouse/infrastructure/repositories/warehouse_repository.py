from typing import List, Optional
from django.db import transaction
from django.db.models import F
from apps.warehouse.core.domain.entities import MaterialEntity, LoanRequestEntity, LoanDetailEntity
from apps.warehouse.core.domain.repositories import IMaterialRepository, ILoanRequestRepository
from apps.warehouse.infrastructure.models import Material, MaterialImage, LoanRequest, LoanDetail

class DjangoMaterialRepository(IMaterialRepository):
    def get_all(self) -> List[MaterialEntity]:
        models = Material.objects.prefetch_related('images').order_by('name')
        return [self._to_entity(m) for m in models]

    def get_by_id(self, material_id: int) -> Optional[MaterialEntity]:
        try:
            return self._to_entity(Material.objects.get(id=material_id))
        except Material.DoesNotExist:
            return None

    def update_stock(self, material_id: int, new_stock: int) -> bool:
        return Material.objects.filter(id=material_id).update(stock=new_stock) > 0

    def decrease_stock(self, material_id: int, quantity: int) -> bool:
        if quantity <= 0:
            return False
        return Material.objects.filter(
            id=material_id,
            stock__gte=quantity,
        ).update(stock=F('stock') - quantity) > 0

    def increase_stock(self, material_id: int, quantity: int) -> bool:
        if quantity <= 0:
            return False
        return Material.objects.filter(id=material_id).update(
            stock=F('stock') + quantity
        ) > 0

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
        
        if material.new_image_paths:
            has_main_image = model.images.filter(is_main=True).exists()
            for index, image_path in enumerate(material.new_image_paths):
                MaterialImage.objects.create(
                    material=model,
                    image=image_path,
                    is_main=not has_main_image and index == 0,
                )
            
        return self._to_entity(model)

    def delete(self, material_id: int) -> bool:
        try:
            material = Material.objects.get(id=material_id)
            material.delete()
            return True
        except Material.DoesNotExist:
            return False

    @transaction.atomic
    def delete_image(self, material_id: int, image_id: int) -> bool:
        image = MaterialImage.objects.filter(
            pk=image_id,
            material_id=material_id,
        ).first()
        if not image:
            return False

        was_main = image.is_main
        image_name = image.image.name
        image_storage = image.image.storage
        image.delete()
        if was_main:
            replacement = MaterialImage.objects.filter(material_id=material_id).order_by('pk').first()
            if replacement:
                replacement.is_main = True
                replacement.save(update_fields=['is_main'])
        transaction.on_commit(lambda: image_storage.delete(image_name))
        return True

    def _to_entity(self, model: Material) -> MaterialEntity:
        images = list(model.images.all())
        images.sort(key=lambda item: (not item.is_main, item.pk))
        image_urls = [item.image.url for item in images if item.image]
        image_items = [
            {'id': item.pk, 'url': item.image.url, 'is_main': item.is_main}
            for item in images if item.image
        ]
        main_img = next((item for item in images if item.is_main and item.image), None)
        img_url = main_img.image.url if main_img else (image_urls[0] if image_urls else None)
        
        return MaterialEntity(
            id=model.id, name=model.name, category=model.category, stock=model.stock, unit=model.unit,
            state=model.state, location=model.location, cycle=model.cycle,
            pedagogical_use=model.pedagogical_use,
            main_image_url=img_url,
            image_urls=image_urls,
            image_items=image_items,
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

    def get_by_id_for_update(self, loan_id: int) -> Optional[LoanRequestEntity]:
        try:
            model = LoanRequest.objects.select_for_update().prefetch_related(
                'details__material', 'teacher'
            ).get(id=loan_id)
            return self._to_entity(model)
        except LoanRequest.DoesNotExist:
            return None
