from django.db import models
from django.conf import settings

class Section(models.Model):
    grade = models.CharField('Grado', max_length=20)
    letter = models.CharField('Letra', max_length=50, default="-") # Lo dejamos con un guion por defecto
    name = models.CharField('Denominación', max_length=100)
    year = models.IntegerField('Año Escolar')

    class Meta:
        app_label = 'academics'
        verbose_name = 'Sección'
        verbose_name_plural = 'Secciones'
        # CORRECCIÓN: Ahora la combinación única es Grado + Nombre + Año
        unique_together = ['grade', 'name', 'year']

    def __str__(self):
        if self.letter == "-":
            return f"{self.grade} - {self.name} ({self.year})"
        return f"{self.grade} {self.letter} - {self.name} ({self.year})"

class Parent(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='parent_profile')
    
    class Meta:
        app_label = 'academics'
        verbose_name = 'Apoderado'
        verbose_name_plural = 'Apoderados'

    def __str__(self):
        return f"Apoderado: {self.user.first_name} {self.user.last_name}"

class Student(models.Model):
    dni = models.CharField('DNI', max_length=8, null=True, blank=True)
    first_name = models.CharField('Nombres', max_length=100)
    last_name = models.CharField('Apellidos', max_length=100)
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE, related_name='students', verbose_name='Apoderado')
    section = models.ForeignKey(Section, on_delete=models.PROTECT, related_name='students', verbose_name='Sección')

    class Meta:
        app_label = 'academics'
        verbose_name = 'Alumno'
        verbose_name_plural = 'Alumnos'

    def __str__(self):
        return f"{self.last_name}, {self.first_name}"