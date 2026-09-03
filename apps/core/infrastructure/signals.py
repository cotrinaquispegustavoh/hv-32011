from django.db.models.signals import post_save, post_delete, pre_delete
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.db.utils import ProgrammingError, OperationalError
from apps.core.infrastructure.models import (
    AuditLog,
    InstitutionalAnnouncement,
    InternalNotification,
)
from apps.core.realtime import broadcast_notification
from apps.core.interfaces.middlewares import get_current_user

# Añadimos 'Migration' y 'Group' a la lista de ignorados
IGNORE_MODELS = ['AuditLog', 'InternalNotification', 'Session', 'LogEntry', 'ContentType', 'Permission', 'Migration', 'Group']


@receiver(post_save, sender=InternalNotification)
def emit_internal_notification(sender, instance, created, **kwargs):
    if created:
        broadcast_notification(instance)


@receiver(pre_delete, sender=InstitutionalAnnouncement)
def delete_announcement_notifications(sender, instance, **kwargs):
    """Evita notificaciones con enlaces rotos al eliminar un comunicado."""
    InternalNotification.objects.filter(
        link=f'/comunicados/{instance.pk}/',
    ).delete()

# --- 1. AUDITORÍA DE CRUD ---
@receiver(post_save)
def audit_post_save(sender, instance, created, update_fields=None, **kwargs):
    if sender.__name__ in IGNORE_MODELS:
        return

    # Django actualiza ``last_login`` durante el acceso y la señal específica
    # ``user_logged_in`` ya registra ese evento. Omitir este guardado técnico
    # evita duplicar cada inicio de sesión como una actualización de usuario.
    if (
        sender.__name__ == 'User'
        and not created
        and update_fields
        and set(update_fields) == {'last_login'}
    ):
        return
    
    user = get_current_user()
    action = 'CREATE' if created else 'UPDATE'
    
    if hasattr(instance, 'is_deleted') and not created:
        if instance.is_deleted:
            action = 'DELETE'
        elif getattr(instance, '_restored', False):
            action = 'RESTORE'

    try:
        AuditLog.objects.create(
            user=user if user and user.is_authenticated else None,
            action=action,
            model_name=sender.__name__,
            object_id=str(instance.pk),
            changes={'info': f'Operación automática registrada en {sender.__name__}'}
        )
    except (ProgrammingError, OperationalError):
        # Si la tabla aún no existe (ej. creando BD de pruebas), ignoramos el error
        pass

@receiver(post_delete)
def audit_post_delete(sender, instance, **kwargs):
    if sender.__name__ in IGNORE_MODELS:
        return
        
    user = get_current_user()
    try:
        AuditLog.objects.create(
            user=user if user and user.is_authenticated else None,
            action='HARD_DELETE',
            model_name=sender.__name__,
            object_id=str(instance.pk),
            changes={'info': 'Registro eliminado físicamente de la base de datos'}
        )
    except (ProgrammingError, OperationalError):
        pass

# --- 2. AUDITORÍA DE ACCESO (LOGIN / LOGOUT) ---
@receiver(user_logged_in)
def audit_user_login(sender, request, user, **kwargs):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    ip = x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')
    
    try:
        AuditLog.objects.create(
            user=user,
            action='LOGIN',
            model_name='User',
            object_id=str(user.pk),
            ip_address=ip,
            changes={'info': 'El usuario inició sesión en el sistema.'}
        )
    except (ProgrammingError, OperationalError):
        pass

@receiver(user_logged_out)
def audit_user_logout(sender, request, user, **kwargs):
    if user:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        ip = x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')
        
        try:
            AuditLog.objects.create(
                user=user,
                action='LOGOUT',
                model_name='User',
                object_id=str(user.pk),
                ip_address=ip,
                changes={'info': 'El usuario cerró su sesión.'}
            )
        except (ProgrammingError, OperationalError):
            pass
