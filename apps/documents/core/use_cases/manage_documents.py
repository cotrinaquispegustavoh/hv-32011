from typing import List
from apps.documents.core.domain.entities import DocumentEntity
from apps.documents.core.domain.repositories import IDocumentRepository

class GetAccessibleDocumentsUseCase:
    def __init__(self, document_repo: IDocumentRepository):
        self.document_repo = document_repo

    def execute(self, user_role: str) -> List[DocumentEntity]:
        return self.document_repo.get_all_accessible(user_role)