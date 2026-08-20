from typing import Optional
from apps.warehouse.core.domain.entities import MaterialEntity
from apps.warehouse.core.domain.repositories import IMaterialRepository

class SaveMaterialUseCase:
    def __init__(self, material_repo: IMaterialRepository):
        self.material_repo = material_repo

    def execute(self, material_id: Optional[int], name: str, category: str, stock: int, unit: str, state: str, location: str, cycle: str, pedagogical_use: str, image_path: Optional[str] = None) -> MaterialEntity:
        material = MaterialEntity(
            id=material_id,
            name=name,
            category=category,
            stock=stock,
            unit=unit,
            state=state,
            location=location,
            cycle=cycle,
            pedagogical_use=pedagogical_use,
            new_image_path=image_path # Pasamos la nueva imagen si existe
        )
        return self.material_repo.save(material)

class DeleteMaterialUseCase:
    def __init__(self, material_repo: IMaterialRepository):
        self.material_repo = material_repo

    def execute(self, material_id: int) -> bool:
        return self.material_repo.delete(material_id)