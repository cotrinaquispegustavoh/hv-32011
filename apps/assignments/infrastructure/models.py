from django.db import models
from django.conf import settings
from apps.academics.infrastructure.models import Section

class TeacherAssignment(models.Model):
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='assignments',
        verbose_name='Docente'
    )
    section = models.ForeignKey(
        Section, 
        on_delete=models.CASCADE, 
        related_name='assignments',
        verbose_name='Sección'
    )
    area = models.CharField('Área / Curso', max_length=100)
    academic_year = models.IntegerField('Año Escolar')

    class Meta:
        app_label = 'assignments'
        verbose_name = 'Asignación Docente'
        verbose_name_plural = 'Asignaciones Docentes'
        # Evita que un docente sea asignado dos veces al mismo curso en la misma aula el mismo año
        unique_together = ['teacher', 'section', 'area', 'academic_year']

    def __str__(self):
        return f"{self.teacher} - {self.area} en {self.section}"