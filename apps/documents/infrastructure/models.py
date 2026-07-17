from django.db import models
from django.conf import settings
from apps.core.infrastructure.models import SoftDeleteModel

class DocumentCategory(models.Model):
    name = models.CharField('Nombre de Categoría', max_length=100, unique=True)
    description = models.TextField('Descripción', blank=True, null=True)

    class Meta:
        app_label = 'documents'
        verbose_name = 'Categoría Documental'
        verbose_name_plural = 'Categorías Documentales'

    def __str__(self):
        return self.name

class InstitutionalDocument(SoftDeleteModel):
    ACCESS_LEVELS = [
        ('PUBLIC', 'Público (Toda la comunidad)'),
        ('STAFF', 'Interno (Solo Personal)'),
        ('DIRECTIVE', 'Confidencial (Solo Directivos)'),
    ]

    title = models.CharField('Título del Documento', max_length=255)
    category = models.ForeignKey(DocumentCategory, on_delete=models.PROTECT, related_name='documents')
    access_level = models.CharField('Nivel de Acceso', max_length=20, choices=ACCESS_LEVELS, default='STAFF')
    tags = models.CharField('Etiquetas (separadas por coma)', max_length=255, blank=True, null=True)
    
    # El archivo actual siempre será la última versión subida
    current_file = models.FileField('Archivo Actual', upload_to='institutional_docs/')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField('Fecha de creación', auto_now_add=True)
    updated_at = models.DateTimeField('Última actualización', auto_now=True)

    class Meta:
        app_label = 'documents'
        verbose_name = 'Documento Institucional'
        verbose_name_plural = 'Documentos Institucionales'
        ordering = ['-updated_at']

    def __str__(self):
        return self.title

class DocumentVersion(models.Model):
    document = models.ForeignKey(InstitutionalDocument, on_delete=models.CASCADE, related_name='versions')
    file = models.FileField('Archivo Histórico', upload_to='institutional_docs/versions/')
    version_number = models.PositiveIntegerField('Número de Versión')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField('Fecha de subida', auto_now_add=True)
    change_summary = models.CharField('Resumen de cambios', max_length=255, blank=True, null=True)

    class Meta:
        app_label = 'documents'
        verbose_name = 'Versión de Documento'
        verbose_name_plural = 'Versiones de Documentos'
        ordering = ['-version_number']

    def __str__(self):
        return f"{self.document.title} - v{self.version_number}"