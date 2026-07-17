from typing import Dict, Any, Tuple
from apps.warehouse.core.domain.entities import MaterialEntity
from apps.warehouse.core.domain.repositories import IMaterialRepository

class ImportMaterialUseCase:
    def __init__(self, material_repo: IMaterialRepository):
        self.material_repo = material_repo

    def execute(self, row_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Recibe un diccionario con los datos de una fila del CSV.
        Retorna una tupla: (True si fue creado / False si fue actualizado, Nombre del material)
        """
        # Limpieza básica de datos
        name = str(row_data.get('nombre', '')).strip()
        if not name:
            raise ValueError("El material no tiene nombre.")

        category = str(row_data.get('categoria', 'General')).strip()
        unit = str(row_data.get('unidad_medida', 'unidades')).strip().lower()
        state = str(row_data.get('estado', 'OPERATIVO')).strip().upper()
        location = str(row_data.get('ubicacion', 'ALMACÉN')).strip()
        pedagogical_use = str(row_data.get('uso_pedagogico', '')).strip()
        
        # Parseo seguro de enteros
        try:
            stock = int(row_data.get('cantidad_disponible', 0) or row_data.get('cantidad_total', 0) or 0)
        except ValueError:
            stock = 0

        # Mapeo del ciclo
        ciclo_raw = str(row_data.get('ciclo', 'Todos')).strip().lower()
        if 'iii' in ciclo_raw or '3' in ciclo_raw:
            cycle = 'III'
        elif 'iv' in ciclo_raw or '4' in ciclo_raw:
            cycle = 'IV'
        elif 'v' in ciclo_raw or '5' in ciclo_raw:
            cycle = 'V'
        else:
            cycle = 'TODOS'

        # Buscamos si el material ya existe para actualizarlo, o lo creamos
        existing_material = self.material_repo.get_by_name(name)
        
        if existing_material:
            # Actualizar
            existing_material.stock = stock
            existing_material.unit = unit
            existing_material.state = state
            existing_material.location = location
            existing_material.cycle = cycle
            existing_material.pedagogical_use = pedagogical_use
            self.material_repo.save(existing_material)
            return False, name
        else:
            # Crear nuevo
            new_material = MaterialEntity(
                id=None,
                name=name,
                stock=stock,
                unit=unit,
                state=state,
                location=location,
                cycle=cycle,
                pedagogical_use=pedagogical_use
            )
            self.material_repo.save(new_material)
            return True, name