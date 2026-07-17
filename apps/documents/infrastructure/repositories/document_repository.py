from typing import List, Optional
from django.db import transaction
from apps.documents.core.domain.entities import DocumentEntity, DocumentVersionEntity
from apps.documents.core.domain.repositories import IDocumentRepository
from apps.documents.infrastructure.models import InstitutionalDocument, DocumentVersion

class DjangoDocumentRepository(IDocumentRepository):
    def _to_entity(self, model: InstitutionalDocument) -> DocumentEntity:
        versions = [
            DocumentVersionEntity(
                id=v.id, document_id=v.document_id, file_path=v.file.name,
                version_number=v.version_number, 
                uploaded_by_name=f"{v.uploaded_by.first_name} {v.uploaded_by.last_name}",
                created_at=v.created_at, change_summary=v.change_summary
            ) for v in model.versions.all()
        ]
        return DocumentEntity(
            id=model.id, title=model.title, category_name=model.category.name,
            category_id=model.category_id, access_level=model.access_level,
            tags=model.tags or "", 
            current_file_path=model.current_file.name if model.current_file else "",
            uploaded_by_name=f"{model.uploaded_by.first_name} {model.uploaded_by.last_name}",
            created_at=model.created_at, updated_at=model.updated_at, versions=versions
        )

    def get_all_accessible(self, user_role: str) -> List[DocumentEntity]:
        # Filtro de seguridad por rol
        if user_role in ['DIRECTOR', 'SUBDIRECTOR', 'SUPERUSER']:
            models = InstitutionalDocument.objects.all()
        elif user_role in ['DOCENTE', 'APOYO']:
            models = InstitutionalDocument.objects.filter(access_level__in=['PUBLIC', 'STAFF'])
        else:
            models = InstitutionalDocument.objects.filter(access_level='PUBLIC')
            
        models = models.select_related('category', 'uploaded_by').prefetch_related('versions__uploaded_by')
        return [self._to_entity(m) for m in models]

    def get_by_id(self, document_id: int) -> Optional[DocumentEntity]:
        try:
            model = InstitutionalDocument.objects.select_related('category', 'uploaded_by').get(id=document_id)
            return self._to_entity(model)
        except InstitutionalDocument.DoesNotExist:
            return None

    @transaction.atomic
    def save_new_version(self, document_id: int, file_path: str, user_id: int, summary: str) -> bool:
        doc = InstitutionalDocument.objects.get(id=document_id)
        
        # Calcular el nuevo número de versión
        last_version = doc.versions.first()
        new_version_num = (last_version.version_number + 1) if last_version else 2
        
        # Crear el historial
        DocumentVersion.objects.create(
            document=doc, file=file_path, version_number=new_version_num,
            uploaded_by_id=user_id, change_summary=summary
        )
        
        # Actualizar el documento principal
        doc.current_file = file_path
        doc.save()
        return True