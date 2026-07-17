from django.contrib import admin
from .infrastructure.models import DocumentCategory, InstitutionalDocument, DocumentVersion

@admin.register(DocumentCategory)
class DocumentCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')

@admin.register(InstitutionalDocument)
class InstitutionalDocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'access_level', 'uploaded_by', 'updated_at', 'is_deleted')
    list_filter = ('access_level', 'category', 'is_deleted')
    search_fields = ('title', 'tags')

admin.site.register(DocumentVersion)