from typing import List, Optional
from apps.documents.core.domain.entities import DocumentEntity
from apps.documents.core.domain.repositories import IDocumentRepository

class GetAccessibleDocumentsUseCase:
    def __init__(self, document_repo: IDocumentRepository):
        self.document_repo = document_repo
    def execute(self, user_role: str) -> List[DocumentEntity]:
        return self.document_repo.get_all_accessible(user_role)

class UploadDocumentUseCase:
    def __init__(self, document_repo: IDocumentRepository):
        self.document_repo = document_repo
    def execute(self, title: str, category_id: int, access_level: str, tags: str, file_path: str, user_id: int) -> DocumentEntity:
        doc = DocumentEntity(
            id=None, title=title, category_name="", category_id=category_id,
            access_level=access_level, tags=tags, current_file_path=file_path,
            uploaded_by_name=user_id, created_at=None, updated_at=None, versions=[]
        )
        return self.document_repo.save(doc)

# --- NUEVOS CASOS DE USO ---
class UpdateDocumentUseCase:
    def __init__(self, document_repo: IDocumentRepository):
        self.document_repo = document_repo
    def execute(self, document_id: int, title: str, category_id: int, access_level: str, tags: str, file_path: Optional[str] = None) -> DocumentEntity:
        return self.document_repo.update_document(document_id, title, category_id, access_level, tags, file_path)

class DeleteDocumentUseCase:
    def __init__(self, document_repo: IDocumentRepository):
        self.document_repo = document_repo
    def execute(self, document_id: int) -> bool:
        return self.document_repo.delete_document(document_id)