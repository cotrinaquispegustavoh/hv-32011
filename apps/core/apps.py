import os
import threading
import time
import urllib.request
from django.apps import AppConfig

def ghost_ping():
    """
    Script Fantasma: Hace una petición a la propia web cada 10 minutos (600 segundos)
    para evitar que el servidor gratuito de Render se duerma (Cold Start).
    """
    # Render inyecta automáticamente esta variable con la URL de tu app
    url = os.environ.get('RENDER_EXTERNAL_URL') 
    if not url:
        return # Si no estamos en Render, el fantasma no hace nada

    while True:
        time.sleep(600) # Espera 10 minutos
        try:
            urllib.request.urlopen(url)
            print(f"👻 Fantasma: Ping exitoso a {url} para mantener el servidor despierto.")
        except Exception as e:
            print(f"👻 Fantasma: Error en el ping - {e}")

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'

    def ready(self):
        # 1. Importamos las señales para que el motor de auditoría arranque
        import apps.core.infrastructure.signals

        # 2. Despertamos al Fantasma (Solo se ejecutará una vez por servidor)
        if os.environ.get('RUN_MAIN') == 'true' or not os.environ.get('RUN_MAIN'):
            # Evitamos que se ejecute doble vez en modo desarrollo
            t = threading.Thread(target=ghost_ping)
            t.daemon = True # El hilo morirá cuando el servidor se apague
            t.start()