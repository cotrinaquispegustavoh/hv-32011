from datetime import timedelta

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.academics.infrastructure.models import Student
from apps.core.infrastructure.models import SoftDeleteModel


class Incident(SoftDeleteModel):
    CATEGORY_SUBTYPES = {
        'CONDUCTA_INADECUADA': [
            ('DESOBEDIENCIA', 'Desobediencia'),
            ('INTERRUPCION_REITERADA', 'Interrupción reiterada'),
            ('FALTA_RESPETO', 'Falta de respeto'),
            ('CONDUCTA_DISRUPTIVA', 'Conducta disruptiva'),
            ('OTRO', 'Otro'),
        ],
        'AGRESION': [
            ('FISICA', 'Física'),
            ('VERBAL', 'Verbal'),
            ('AMENAZA', 'Amenaza'),
            ('OTRO', 'Otro'),
        ],
        'ACOSO_INTIMIDACION': [
            ('BURLAS_REITERADAS', 'Burlas reiteradas'),
            ('HOSTIGAMIENTO', 'Hostigamiento'),
            ('EXCLUSION_DELIBERADA', 'Exclusión deliberada'),
            ('CIBERACOSO', 'Ciberacoso'),
            ('OTRO', 'Otro'),
        ],
        'DANO_INCUMPLIMIENTO': [
            ('DANO_BIENES', 'Daño a bienes'),
            ('SUSTRACCION_PERTENENCIAS', 'Sustracción de pertenencias'),
            ('OBJETO_PROHIBIDO', 'Uso de objeto prohibido'),
            ('ZONA_RESTRINGIDA', 'Ingreso a zona restringida'),
            ('INCUMPLIMIENTO_NORMA', 'Incumplimiento de norma'),
            ('OTRO', 'Otro'),
        ],
        'RIESGO_SITUACION_ESPECIAL': [
            ('CONDUCTA_PELIGROSA', 'Conducta peligrosa'),
            ('ACCIDENTE', 'Accidente'),
            ('CRISIS_EMOCIONAL', 'Crisis emocional'),
            ('REQUIERE_SEGUIMIENTO', 'Situación que requiere seguimiento'),
            ('OTRO', 'Otro'),
        ],
    }
    CATEGORY_CHOICES = [
        ('CONDUCTA_INADECUADA', 'Conducta inadecuada'),
        ('AGRESION', 'Agresión'),
        ('ACOSO_INTIMIDACION', 'Acoso o intimidación'),
        ('DANO_INCUMPLIMIENTO', 'Daño o incumplimiento de normas'),
        ('RIESGO_SITUACION_ESPECIAL', 'Riesgo o situación especial'),
    ]
    SUBTYPE_CHOICES = list(dict.fromkeys(
        choice
        for choices in CATEGORY_SUBTYPES.values()
        for choice in choices
    ))
    SEVERITY_CHOICES = [
        ('LEVE', 'Leve'),
        ('MODERADA', 'Moderada'),
        ('GRAVE', 'Grave'),
    ]
    LOCATION_CHOICES = [
        ('AULA', 'Aula'),
        ('PATIO', 'Patio'),
        ('PASILLO', 'Pasillo'),
        ('SERVICIOS_HIGIENICOS', 'Servicios higiénicos'),
        ('BIBLIOTECA', 'Biblioteca'),
        ('AREA_DEPORTIVA', 'Área deportiva'),
        ('INGRESO_SALIDA', 'Ingreso / salida'),
        ('OTRO', 'Otro'),
    ]
    REFERRAL_CHOICES = [
        ('TUTOR', 'Tutor'),
        ('DIRECCION', 'Dirección'),
        ('SUBDIRECCION', 'Subdirección'),
        ('PSICOPEDAGOGIA', 'Psicopedagogía'),
    ]
    STATUS_CHOICES = [
        ('REGISTRADA', 'Registrada'),
        ('EN_SEGUIMIENTO', 'En seguimiento'),
        ('CERRADA', 'Cerrada'),
    ]

    code = models.CharField(
        'Código', max_length=24, unique=True, null=True, blank=True, editable=False,
    )
    student = models.ForeignKey(
        Student,
        on_delete=models.PROTECT,
        related_name='incidents',
        verbose_name='Alumno',
    )
    additional_students = models.ManyToManyField(
        Student,
        related_name='secondary_incidents',
        verbose_name='Estudiantes adicionales',
        blank=True,
    )
    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, verbose_name='Reportado por')
    occurred_at = models.DateTimeField('Fecha y hora de la incidencia', default=timezone.now)
    location = models.CharField('Lugar', max_length=30, choices=LOCATION_CHOICES, default='AULA')
    other_location = models.CharField('Otro lugar', max_length=120, blank=True)
    category = models.CharField(
        'Categoría', max_length=40, choices=CATEGORY_CHOICES,
        default='CONDUCTA_INADECUADA',
    )
    severity = models.CharField('Gravedad', max_length=10, choices=SEVERITY_CHOICES)
    subtype = models.CharField('Subtipo', max_length=40, choices=SUBTYPE_CHOICES)
    legacy_subtype = models.CharField(
        'Clasificación histórica original', max_length=20, blank=True, editable=False,
    )
    description = models.TextField('Descripción de los hechos')
    additional_people = models.TextField('Otras personas involucradas', blank=True)
    immediate_action = models.TextField('Acción inmediata realizada', default='')
    requires_follow_up = models.BooleanField('Requiere seguimiento', default=False)
    referred_to = models.CharField(
        'Derivar a', max_length=30, choices=REFERRAL_CHOICES, blank=True,
    )
    additional_observations = models.TextField('Observaciones adicionales', blank=True)
    status = models.CharField(
        'Estado', max_length=20, choices=STATUS_CHOICES,
        default='REGISTRADA',
    )
    academic_year = models.PositiveIntegerField('Año académico', null=True, editable=False)
    date_reported = models.DateTimeField('Fecha de reporte', auto_now_add=True)
    updated_at = models.DateTimeField('Última modificación', auto_now=True)

    class Meta:
        app_label = 'discipline'
        verbose_name = 'Incidencia'
        verbose_name_plural = 'Incidencias'
        indexes = [
            models.Index(fields=['category', 'subtype'], name='incident_category_idx'),
            models.Index(fields=['severity', 'occurred_at'], name='incident_severity_idx'),
            models.Index(fields=['academic_year', 'status'], name='incident_year_status_idx'),
        ]

    def clean(self):
        super().clean()
        if self.occurred_at and self.occurred_at > timezone.now() + timedelta(minutes=5):
            raise ValidationError({
                'occurred_at': 'La fecha de la incidencia no puede estar en el futuro.',
            })
        valid_subtypes = {
            value for value, _label in self.CATEGORY_SUBTYPES.get(self.category, [])
        }
        if self.subtype and self.subtype not in valid_subtypes:
            raise ValidationError({
                'subtype': 'El subtipo no corresponde a la categoría seleccionada.',
            })
        if self.location == 'OTRO' and not self.other_location.strip():
            raise ValidationError({'other_location': 'Debes especificar el lugar.'})
        if self.requires_follow_up and not self.referred_to:
            raise ValidationError({'referred_to': 'Debes indicar el área de derivación.'})
        if not self.requires_follow_up:
            self.referred_to = ''

    def save(self, *args, **kwargs):
        if not self.academic_year and self.student_id:
            self.academic_year = self.student.section.year
        super().save(*args, **kwargs)
        if not self.code:
            year = self.academic_year or timezone.localtime(self.occurred_at).year
            self.code = f'INC-{year}-{self.pk:06d}'
            type(self).all_objects.filter(pk=self.pk).update(code=self.code)

    def __str__(self):
        return f"{self.code or 'INC'} - {self.get_severity_display()} - {self.student}"

class Evidence(models.Model):
    incident = models.ForeignKey(Incident, on_delete=models.CASCADE, related_name='evidences')
    file = models.FileField('Archivo de evidencia', upload_to='discipline_evidences/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'discipline'
        verbose_name = 'Evidencia'
        verbose_name_plural = 'Evidencias'
