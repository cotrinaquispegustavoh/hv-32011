from django.core.management.base import BaseCommand
from apps.users.infrastructure.models import User
from apps.academics.infrastructure.models import Section, Parent, Student

class Command(BaseCommand):
    help = 'Puebla la base de datos con las semillas iniciales según el PRD'

    def handle(self, *args, **kwargs):
        self.stdout.write('Iniciando carga de semillas...')

        # 1. Crear Usuarios
        users_data = [
            {'dni': '00000000', 'role': 'SUPERUSER', 'first': 'Superuser', 'last': 'Técnico', 'support_role': None},
            {'dni': '11111111', 'role': 'DIRECTOR', 'first': 'Carlos', 'last': 'Director', 'support_role': None},
            {'dni': '22222222', 'role': 'SUBDIRECTOR', 'first': 'Ana', 'last': 'Subdir Uno', 'support_role': None},
            {'dni': '33333333', 'role': 'SUBDIRECTOR', 'first': 'Luis', 'last': 'Subdir Dos', 'support_role': None},
            {'dni': '44444444', 'role': 'DOCENTE', 'first': 'María', 'last': 'Docente Uno', 'support_role': None},
            {'dni': '55555555', 'role': 'DOCENTE', 'first': 'Jorge', 'last': 'Docente Dos', 'support_role': None},
            {'dni': '66666666', 'role': 'APODERADO', 'first': 'Rosa', 'last': 'Apoderado Uno', 'support_role': None},
            {'dni': '77777777', 'role': 'APODERADO', 'first': 'Pedro', 'last': 'Apoderado Dos', 'support_role': None},
            {'dni': '88888888', 'role': 'APOYO', 'first': 'Roberto', 'last': 'Apoyo Uno', 'support_role': 'Encargado de Almacén'},
        ]

        for u in users_data:
            user, created = User.objects.get_or_create(
                dni=u['dni'],
                defaults={
                    'role': u['role'],
                    'first_name': u['first'],
                    'last_name': u['last'],
                    'support_role': u['support_role'],
                    'password_changed': False
                }
            )
            if created:
                user.set_password(u['dni'])
                user.save()
                self.stdout.write(self.style.SUCCESS(f"Usuario creado: {u['role']} - {u['dni']}"))

        # 2. Crear Secciones de prueba
        sections_data = [
            {'grade': '1ro', 'letter': 'A', 'name': 'Respeto', 'year': 2026},
            {'grade': '2do', 'letter': 'B', 'name': 'Solidaridad', 'year': 2026},
        ]

        secciones_creadas = []
        for s in sections_data:
            section, _ = Section.objects.get_or_create(
                grade=s['grade'], letter=s['letter'], year=s['year'],
                defaults={'name': s['name']}
            )
            secciones_creadas.append(section)
            self.stdout.write(self.style.SUCCESS(f"Sección creada: {s['grade']} {s['letter']}"))

        # 3. Crear Apoderados (Perfiles vinculados al User) y Alumnos
        try:
            user_apoderado_1 = User.objects.get(dni='66666666')
            user_apoderado_2 = User.objects.get(dni='77777777')

            parent_1, _ = Parent.objects.get_or_create(user=user_apoderado_1)
            parent_2, _ = Parent.objects.get_or_create(user=user_apoderado_2)

            # Crear Alumno 1
            Student.objects.get_or_create(
                first_name='Juanito',
                last_name='Pérez',
                parent=parent_1,
                section=secciones_creadas[0]
            )
            self.stdout.write(self.style.SUCCESS("Alumno creado: Juanito Pérez"))

            # Crear Alumno 2
            Student.objects.get_or_create(
                first_name='Anita',
                last_name='Gómez',
                parent=parent_2,
                section=secciones_creadas[1]
            )
            self.stdout.write(self.style.SUCCESS("Alumno creado: Anita Gómez"))

        except User.DoesNotExist:
            self.stdout.write(self.style.WARNING("No se encontraron los usuarios apoderados para crear alumnos."))

        self.stdout.write(self.style.SUCCESS('¡Semillas cargadas con éxito!'))