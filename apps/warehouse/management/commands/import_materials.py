import csv
import os
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.warehouse.infrastructure.repositories.warehouse_repository import DjangoMaterialRepository
from apps.warehouse.core.use_cases.import_materials import ImportMaterialUseCase

class Command(BaseCommand):
    help = 'Importa materiales desde un archivo CSV delimitado por punto y coma (;)'

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str, required=True, help='Ruta absoluta o relativa del archivo CSV')

    def handle(self, *args, **options):
        csv_path = options['file']
        
        if not os.path.exists(csv_path):
            self.stderr.write(self.style.ERROR(f'ERROR: Archivo no encontrado en {csv_path}'))
            return

        self.stdout.write(self.style.WARNING(f'>>> Procesando archivo: {csv_path}'))

        repo = DjangoMaterialRepository()
        use_case = ImportMaterialUseCase(repo)
        
        creados = 0
        actualizados = 0

        try:
            # utf-8-sig ignora los caracteres BOM invisibles de Excel
            with open(csv_path, encoding='utf-8-sig') as f:
                reader = csv.DictReader(f, delimiter=';')
                
                # Limpiamos las cabeceras por si tienen espacios
                if reader.fieldnames:
                    reader.fieldnames = [str(c).strip().lower().replace(' ', '_') for c in reader.fieldnames if c]

                with transaction.atomic():
                    for idx, row in enumerate(reader, start=2):
                        try:
                            created, name = use_case.execute(row)
                            if created:
                                creados += 1
                                self.stdout.write(f"Creado: {name}")
                            else:
                                actualizados += 1
                                self.stdout.write(f"Actualizado: {name}")
                        except ValueError as ve:
                            self.stderr.write(self.style.ERROR(f'Fila {idx} saltada: {str(ve)}'))

            self.stdout.write(self.style.SUCCESS(
                f'\n>>> ÉXITO TOTAL: {creados} Creados | {actualizados} Actualizados.'
            ))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f'FALLO CRÍTICO DE IMPORTACIÓN: {str(e)}'))