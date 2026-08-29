import json
import urllib.request
from datetime import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.core.infrastructure.models import InstitutionalEvent

class Command(BaseCommand):
    help = 'Descarga los feriados nacionales de Perú y los guarda en el calendario institucional'

    def handle(self, *args, **kwargs):
        # Obtenemos el año actual automáticamente (Ej: 2026)
        year = timezone.now().year
        
        # API pública y gratuita de feriados mundiales (PE = Perú)
        url = f"https://date.nager.at/api/v3/PublicHolidays/{year}/PE"
        
        self.stdout.write(self.style.WARNING(f">>> Conectando a la base de datos global para el año {year}..."))
        
        try:
            # Hacemos la petición a la API
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                
                creados = 0
                for item in data:
                    # La API devuelve la fecha en formato YYYY-MM-DD
                    event_date = datetime.strptime(item['date'], '%Y-%m-%d').date()
                    title = item['localName'] # Ej: "Santa Rosa de Lima"
                    
                    # Usamos get_or_create para no duplicar feriados si corres el comando 2 veces
                    obj, created = InstitutionalEvent.objects.get_or_create(
                        event_date=event_date,
                        title=title,
                        defaults={
                            'description': 'Feriado Nacional (Calendario Oficial de Perú)',
                            'is_holiday': True
                        }
                    )
                    
                    if created:
                        creados += 1
                        self.stdout.write(self.style.SUCCESS(f"Feriado añadido: {title} ({event_date.strftime('%d/%m/%Y')})"))
                        
                self.stdout.write(self.style.SUCCESS(f"\n>>> ¡Proceso completado! {creados} feriados nuevos añadidos a la agenda."))
                
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error al obtener los feriados: {e}"))