from django.db import models
from django.conf import settings
from django.utils import timezone

# ==========================================
# CLASES BASE (SOFT DELETE)
# ==========================================
class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)
    
    def all_with_deleted(self):
        return super().get_queryset()
        
    def deleted_only(self):
        return super().get_queryset().filter(is_deleted=True)

class SoftDeleteModel(models.Model):
    is_deleted = models.BooleanField('Eliminado', default=False)
    deleted_at = models.DateTimeField('Fecha de eliminación', null=True, blank=True)

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def delete(self, hard=False, *args, **kwargs):
        if hard:
            super().delete(*args, **kwargs)
        else:
            self.is_deleted = True
            self.deleted_at = timezone.now()
            self.save()

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.save()

# ==========================================
# MODELOS DEL CORE
# ==========================================
class InternalNotification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField('Título', max_length=200)
    message = models.TextField('Mensaje')
    link = models.CharField('Enlace', max_length=255, blank=True, null=True)
    is_read = models.BooleanField('Leída', default=False)
    created_at = models.DateTimeField('Fecha de creación', auto_now_add=True)

    class Meta:
        app_label = 'core'
        verbose_name = 'Notificación Interna'
        verbose_name_plural = 'Notificaciones Internas'
        ordering = ['-created_at']

    def __str__(self):
        return f"Para {self.user}: {self.title}"

class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('CREATE', 'Creación'),
        ('UPDATE', 'Actualización'),
        ('DELETE', 'Eliminación Lógica'),
        ('HARD_DELETE', 'Eliminación Física'),
        ('RESTORE', 'Restauración'),
        ('LOGIN', 'Inicio de Sesión'),
        ('LOGOUT', 'Cierre de Sesión'),
        ('PERMISSIONS', 'Cambio de Permisos'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField('Acción', max_length=15, choices=ACTION_CHOICES)
    model_name = models.CharField('Tabla/Modelo', max_length=100)
    object_id = models.CharField('ID del Registro', max_length=50)
    changes = models.JSONField('Cambios / Estado', blank=True, null=True)
    timestamp = models.DateTimeField('Fecha y Hora', auto_now_add=True)
    ip_address = models.GenericIPAddressField('Dirección IP', blank=True, null=True)

    class Meta:
        app_label = 'core'
        verbose_name = 'Registro de Auditoría'
        verbose_name_plural = 'Registros de Auditoría'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.action} en {self.model_name} por {self.user}"

class InstitutionalEvent(models.Model):
    title = models.CharField('Título', max_length=200)
    description = models.TextField('Descripción')
    event_date = models.DateField('Fecha del Evento')
    is_holiday = models.BooleanField('Es feriado', default=False)

    class Meta:
        app_label = 'core'
        verbose_name = 'Evento Institucional'
        verbose_name_plural = 'Eventos Institucionales'
        ordering = ['event_date']

    def __str__(self):
        return f"{self.title} - {self.event_date}"