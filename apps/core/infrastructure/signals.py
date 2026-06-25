from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from apps.core.infrastructure.models import AuditLog
from apps.core.interfaces.middlewares import get_current_user

# Tablas que NO queremos auditar para evitar bucles infinitos o basura
IGNORE_MODELS = ['AuditLog', 'InternalNotification', 'Session', 'LogEntry', 'ContentType', 'Permission']

@receiver(post_save)
def audit_post_save(sender, instance, created, **kwargs):
    if sender.__name__ in IGNORE_MODELS:
        return
    
    user = get_current_user()
    action = 'CREATE' if created else 'UPDATE'
    
    # Detectar si fue un Soft Delete o una Restauración
    if hasattr(instance, 'is_deleted') and not created:
        # Si el campo is_deleted acaba de cambiar (esto requeriría lógica extra para ser exacto, 
        # pero por ahora asumimos el estado actual)
        if instance.is_deleted:
            action = 'DELETE'
        elif getattr(instance, '_restored', False): # Bandera temporal opcional
            action = 'RESTORE'

    # Guardar el registro silenciosamente
    AuditLog.objects.create(
        user=user if user and user.is_authenticated else None,
        action=action,
        model_name=sender.__name__,
        object_id=str(instance.pk),
        changes={'info': f'Operación automática registrada en {sender.__name__}'}
    )

@receiver(post_delete)
def audit_post_delete(sender, instance, **kwargs):
    if sender.__name__ in IGNORE_MODELS:
        return
        
    user = get_current_user()
    AuditLog.objects.create(
        user=user if user and user.is_authenticated else None,
        action='HARD_DELETE',
        model_name=sender.__name__,
        object_id=str(instance.pk),
        changes={'info': 'Registro eliminado físicamente de la base de datos'}
    )