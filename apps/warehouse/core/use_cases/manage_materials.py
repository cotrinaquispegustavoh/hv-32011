from typing import Optional
from apps.warehouse.core.domain.entities import MaterialEntity
from apps.warehouse.core.domain.repositories import IMaterialRepository

class SaveMaterialUseCase:
    def __init__(self, material_repo: IMaterialRepository):
        self.material_repo = material_repo

    def execute(self, material_id: Optional[int], name: str, stock: int, unit: str, state: str, location: str, cycle: str, pedagogical_use: str) -> MaterialEntity:
        material = MaterialEntity(
            id=material_id,
            name=name,
            stock=stock,
            unit=unit,
            state=state,
            location=location,
            cycle=cycle,
            pedagogical_use=pedagogical_use
        )
        return self.material_repo.save(material)

class DeleteMaterialUseCase:
    def __init__(self, material_repo: IMaterialRepository):
        self.material_repo = material_repo

    def execute(self, material_id: int) -> bool:
        return self.material_repo.delete(material_id)