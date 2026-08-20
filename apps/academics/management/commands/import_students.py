import csv
import os
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from apps.users.infrastructure.repositories.user_repository import DjangoUserRepository
from apps.academics.infrastructure.repositories.academics_repository import DjangoSectionRepository, DjangoParentRepository, DjangoStudentRepository
from apps.academics.core.use_cases.import_students import ImportStudentsUseCase

class Command(BaseCommand):
    help = 'Importa alumnos y apoderados desde un archivo CSV delimitado por punto y coma (;)'

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str, required=True, help='Ruta del archivo CSV')

    def handle(self, *args, **options):
        csv_path = options['file']
        if not os.path.exists(csv_path):
            self.stderr.write(self.style.ERROR(f'ERROR: Archivo no encontrado en {csv_path}'))
            return

        user_repo = DjangoUserRepository()
        section_repo = DjangoSectionRepository()
        parent_repo = DjangoParentRepository()
        student_repo = DjangoStudentRepository()
        use_case = ImportStudentsUseCase(user_repo, section_repo, parent_repo, student_repo)

        current_year = timezone.now().year
        creados = 0
        errores = 0

        self.stdout.write(self.style.WARNING(f'>>> Procesando matrícula para el año {current_year}...'))

        try:
            with open(csv_path, encoding='utf-8-sig') as f:
                reader = csv.DictReader(f, delimiter=';')
                if reader.fieldnames:
                    reader.fieldnames = [str(c).strip().lower().replace(' ', '_') for c in reader.fieldnames if c]

                with transaction.atomic():
                    for idx, row in enumerate(reader, start=2):
                        try:
                            _, name = use_case.execute(row, current_year)
                            creados += 1
                            self.stdout.write(f"Matriculado: {name}")
                        except Exception as e:
                            errores += 1
                            self.stderr.write(self.style.ERROR(f'Fila {idx} saltada: {str(e)}'))

            self.stdout.write(self.style.SUCCESS(f'\n>>> ÉXITO: {creados} Alumnos importados. Errores: {errores}'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'FALLO CRÍTICO: {str(e)}'))