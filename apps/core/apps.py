from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'

    def ready(self):
        # Importamos las señales para que el motor de auditoría arranque
        import apps.core.infrastructure.signals