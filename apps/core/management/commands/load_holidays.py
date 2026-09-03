import json
import urllib.request
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.core.infrastructure.models import InstitutionalEvent


API_DESCRIPTION = 'Feriado Nacional (Nager.Date - Perú)'


class Command(BaseCommand):
    help = 'Descarga los feriados nacionales de Perú y los guarda en el calendario institucional'

    def add_arguments(self, parser):
        parser.add_argument(
            '--year',
            type=int,
            default=timezone.localdate().year,
            help='Año inicial que se descargará.',
        )
        parser.add_argument(
            '--years-ahead',
            type=int,
            default=0,
            help='Cantidad de años adicionales que se descargarán.',
        )
        parser.add_argument(
            '--strict',
            action='store_true',
            help='Interrumpe el proceso si la API no está disponible.',
        )

    def handle(self, *args, **options):
        start_year = options['year']
        years_ahead = max(options['years_ahead'], 0)
        created_total = 0

        for year in range(start_year, start_year + years_ahead + 1):
            try:
                created_total += self._load_year(year)
            except Exception as exc:
                message = f'No se pudieron obtener los feriados de Perú para {year}: {exc}'
                if options['strict']:
                    raise CommandError(message) from exc
                self.stderr.write(self.style.ERROR(message))

        self.stdout.write(self.style.SUCCESS(
            f'Proceso completado: {created_total} feriados nuevos añadidos.',
        ))

    def _load_year(self, year):
        url = f'https://date.nager.at/api/v3/PublicHolidays/{year}/PE'
        self.stdout.write(f'Consultando feriados nacionales de Perú para {year}...')
        request = urllib.request.Request(
            url,
            headers={'User-Agent': 'I.E.-32011-Intranet/1.0'},
        )
        with urllib.request.urlopen(request, timeout=20) as response:
            data = json.loads(response.read().decode('utf-8'))

        created_count = 0
        for item in data:
            if item.get('global') is False:
                continue
            event_date = datetime.strptime(item['date'], '%Y-%m-%d').date()
            if InstitutionalEvent.objects.filter(
                event_date=event_date,
                is_holiday=True,
            ).exists():
                continue
            InstitutionalEvent.objects.create(
                event_date=event_date,
                title=item['localName'],
                description=API_DESCRIPTION,
                is_holiday=True,
            )
            created_count += 1
            self.stdout.write(self.style.SUCCESS(
                f'Feriado añadido: {item["localName"]} ({event_date:%d/%m/%Y})',
            ))
        return created_count
