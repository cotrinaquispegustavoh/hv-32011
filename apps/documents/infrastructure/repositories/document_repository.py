from typing import List, Optional
from django.db import transaction
from django.db.models import ProtectedError
from apps.documents.core.domain.entities import DocumentEntity, DocumentVersionEntity, DocumentCategoryEntity
from apps.documents.core.domain.repositories import IDocumentRepository
from apps.documents.infrastructure.models import InstitutionalDocument, DocumentVersion, DocumentCategory

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
        last_version = doc.versions.first()
        new_version_num = (last_version.version_number + 1) if last_version else 2
        
        DocumentVersion.objects.create(
            document=doc, file=file_path, version_number=new_version_num,
            uploaded_by_id=user_id, change_summary=summary
        )
        doc.current_file = file_path
        doc.save()
        return True

    def save(self, document: DocumentEntity) -> DocumentEntity:
        model = InstitutionalDocument.objects.create(
            title=document.title, category_id=document.category_id,
            access_level=document.access_level, tags=document.tags,
            current_file=document.current_file_path, uploaded_by_id=document.uploaded_by_name 
        )
        DocumentVersion.objects.create(
            document=model, file=document.current_file_path, version_number=1,
            uploaded_by_id=document.uploaded_by_name, change_summary="Documento original"
        )
        return self._to_entity(model)

    # --- NUEVAS FUNCIONES: EDITAR Y ELIMINAR DOCUMENTO ---
    @transaction.atomic
    def update_document(self, document_id: int, title: str, category_id: int, access_level: str, tags: str, file_path: Optional[str] = None) -> DocumentEntity:
        doc = InstitutionalDocument.objects.get(id=document_id)
        doc.title = title
        doc.category_id = category_id
        doc.access_level = access_level
        doc.tags = tags
        
        if file_path:
            doc.current_file = file_path
            last_version = doc.versions.first()
            new_version_num = (last_version.version_number + 1) if last_version else 2
            DocumentVersion.objects.create(
                document=doc, file=file_path, version_number=new_version_num,
                uploaded_by_id=doc.uploaded_by_id, change_summary="Actualización de documento"
            )
        doc.save()
        return self._to_entity(doc)

    def delete_document(self, document_id: int) -> bool:
        try:
            doc = InstitutionalDocument.objects.get(id=document_id)
            doc.delete() # Esto ejecuta el Soft Delete que programamos antes
            return True
        except InstitutionalDocument.DoesNotExist:
            return False

    # --- GESTIÓN DE CATEGORÍAS ---
    def get_all_categories(self) -> List[DocumentCategoryEntity]:
        models = DocumentCategory.objects.all().order_by('name')
        return [DocumentCategoryEntity(id=m.id, name=m.name, description=m.description) for m in models]

    def create_category(self, name: str) -> DocumentCategoryEntity:
        model = DocumentCategory.objects.create(name=name)
        return DocumentCategoryEntity(id=model.id, name=model.name, description=model.description)

    def update_category(self, category_id: int, new_name: str) -> DocumentCategoryEntity:
        model = DocumentCategory.objects.get(id=category_id)
        model.name = new_name
        model.save()
        return DocumentCategoryEntity(id=model.id, name=model.name, description=model.description)

    def delete_category(self, category_id: int) -> bool:
        try:
            DocumentCategory.objects.filter(id=category_id).delete()
            return True
        except ProtectedError:
            raise ValueError("No se puede eliminar esta categoría porque tiene documentos asignados. Intenta editar su nombre.")