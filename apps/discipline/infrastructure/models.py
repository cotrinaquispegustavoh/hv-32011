from django.db import models
from django.conf import settings
from apps.academics.infrastructure.models import Student

class Incident(models.Model):
    SEVERITY_CHOICES = [
        ('LEVE', 'Leve'),
        ('MODERADA', 'Moderada'),
        ('GRAVE', 'Grave'),
    ]
    SUBTYPE_CHOICES = [
        ('CONDUCTA', 'Conducta'),
        ('RENDIMIENTO', 'Rendimiento'),
        ('SALUD', 'Salud'),
        ('ASISTENCIA', 'Asistencia'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='incidents', verbose_name='Alumno')
    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, verbose_name='Reportado por')
    
    severity = models.CharField('Gravedad', max_length=10, choices=SEVERITY_CHOICES)
    subtype = models.CharField('Subtipo', max_length=15, choices=SUBTYPE_CHOICES)
    description = models.TextField('Descripción de los hechos')
    date_reported = models.DateTimeField('Fecha de reporte', auto_now_add=True)

    class Meta:
        app_label = 'discipline'
        verbose_name = 'Incidencia'
        verbose_name_plural = 'Incidencias'

    def __str__(self):
        return f"{self.get_severity_display()} - {self.student} ({self.date_reported.strftime('%d/%m/%Y')})"

class Evidence(models.Model):
    incident = models.ForeignKey(Incident, on_delete=models.CASCADE, related_name='evidences')
    file = models.FileField('Archivo de evidencia', upload_to='discipline_evidences/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'discipline'
        verbose_name = 'Evidencia'
        verbose_name_plural = 'Evidencias'