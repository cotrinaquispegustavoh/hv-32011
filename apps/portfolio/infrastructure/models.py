from django.db import models
from django.conf import settings
from apps.core.infrastructure.models import SoftDeleteModel
from apps.academics.infrastructure.models import Section # <-- IMPORTAR SECCIÓN

class PortfolioItem(SoftDeleteModel):
    TYPE_CHOICES = [
        ('TRABAJO', 'Ficha de Trabajo'),
        ('TAREA', 'Ficha de Tarea'),
    ]
    
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='portfolio_items', verbose_name='Docente')
    
    # --- NUEVO CAMPO: Vinculamos la ficha a un aula ---
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='portfolio_items', null=True, blank=True, verbose_name='Sección')
    
    item_type = models.CharField('Tipo de Ficha', max_length=10, choices=TYPE_CHOICES)
    title = models.CharField('Título', max_length=200)
    description = models.TextField('Descripción', blank=True, null=True)
    file = models.FileField('Archivo adjunto', upload_to='portfolio_files/')
    created_at = models.DateTimeField('Fecha de subida', auto_now_add=True)

    class Meta:
        app_label = 'portfolio'
        verbose_name = 'Ficha de Portafolio'
        verbose_name_plural = 'Fichas de Portafolio'

    def __str__(self):
        return f"{self.get_item_type_display()} - {self.title}"

class Observation(models.Model):
    portfolio_item = models.ForeignKey(PortfolioItem, on_delete=models.CASCADE, related_name='observations')
    director = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='made_observations', verbose_name='Director')
    content = models.TextField('Observación')
    created_at = models.DateTimeField('Fecha de observación', auto_now_add=True)

    class Meta:
        app_label = 'portfolio'
        verbose_name = 'Observación Directiva'
        verbose_name_plural = 'Observaciones Directivas'

    def __str__(self):
        return f"Obs. de {self.director} en {self.portfolio_item.title}"