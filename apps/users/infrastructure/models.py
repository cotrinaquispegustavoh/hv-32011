from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

class UserManager(BaseUserManager):
    def create_user(self, dni, password=None, **extra_fields):
        if not dni:
            raise ValueError('El DNI es obligatorio para crear un usuario.')
        user = self.model(dni=dni, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, dni, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'SUPERUSER')
        extra_fields.setdefault('password_changed', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser debe tener is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser debe tener is_superuser=True.')

        return self.create_user(dni, password, **extra_fields)

class User(AbstractUser):
    username = None 
    dni = models.CharField('DNI', max_length=8, unique=True)
    
    ROLE_CHOICES = [
        ('DIRECTOR', 'Director'),
        ('SUBDIRECTOR', 'Subdirector'),
        ('DOCENTE', 'Docente'),
        ('APOYO', 'Personal de Apoyo'),
        ('APODERADO', 'Apoderado'),
        ('SUPERUSER', 'Superuser Técnico'),
    ]
    role = models.CharField('Rol', max_length=20, choices=ROLE_CHOICES)
    support_role = models.CharField('Cargo Específico', max_length=50, blank=True, null=True)
    
    birth_date = models.DateField('Fecha de Nacimiento', null=True, blank=True)
    phone = models.CharField('Teléfono', max_length=20, null=True, blank=True) # <-- NUEVO CAMPO
    
    password_changed = models.BooleanField('Contraseña cambiada', default=False)
    module_permissions = models.JSONField('Permisos de Módulos', default=list, blank=True)

    USERNAME_FIELD = 'dni'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = UserManager()

    class Meta:
        app_label = 'users'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        base_role = self.get_role_display() or self.role
        if self.role == 'APOYO' and self.support_role:
            return f"{self.dni} - {base_role} ({self.support_role})"
        return f"{self.dni} - {base_role}"