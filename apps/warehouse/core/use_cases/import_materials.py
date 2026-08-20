from typing import Dict, Any, Tuple
from apps.warehouse.core.domain.entities import MaterialEntity
from apps.warehouse.core.domain.repositories import IMaterialRepository

class ImportMaterialUseCase:
    def __init__(self, material_repo: IMaterialRepository):
        self.material_repo = material_repo

    def execute(self, row_data: Dict[str, Any]) -> Tuple[bool, str]:
        name = str(row_data.get('nombre', '')).strip()
        if not name:
            raise ValueError("El material no tiene nombre.")

        # CORRECCIÓN: Ahora sí capturamos la categoría del CSV
        category = str(row_data.get('categoria', 'General')).strip()
        unit = str(row_data.get('unidad_medida', 'unidades')).strip().lower()
        state = str(row_data.get('estado', 'OPERATIVO')).strip().upper()
        location = str(row_data.get('ubicacion', 'ALMACÉN')).strip()
        pedagogical_use = str(row_data.get('uso_pedagogico', '')).strip()
        
        try:
            stock = int(row_data.get('cantidad_disponible', 0) or row_data.get('cantidad_total', 0) or 0)
        except ValueError:
            stock = 0

        ciclo_raw = str(row_data.get('ciclo', 'Todos')).strip().lower()
        if 'iii' in ciclo_raw or '3' in ciclo_raw: cycle = 'III'
        elif 'iv' in ciclo_raw or '4' in ciclo_raw: cycle = 'IV'
        elif 'v' in ciclo_raw or '5' in ciclo_raw: cycle = 'V'
        else: cycle = 'TODOS'

        existing_material = self.material_repo.get_by_name(name)
        
        if existing_material:
            existing_material.category = category # <-- GUARDAMOS LA CATEGORÍA
            existing_material.stock = stock
            existing_material.unit = unit
            existing_material.state = state
            existing_material.location = location
            existing_material.cycle = cycle
            existing_material.pedagogical_use = pedagogical_use
            self.material_repo.save(existing_material)
            return False, name
        else:
            new_material = MaterialEntity(
                id=None,
                name=name,
                category=category, # <-- GUARDAMOS LA CATEGORÍA
                stock=stock,
                unit=unit,
                state=state,
                location=location,
                cycle=cycle,
                pedagogical_use=pedagogical_use
            )
            self.material_repo.save(new_material)
            return True, name