from abc import ABC, abstractmethod
from typing import List, Optional
from .entities import DocumentEntity

class IDocumentRepository(ABC):
    @abstractmethod
    def get_all_accessible(self, user_role: str) -> List[DocumentEntity]:
        """Devuelve los documentos según el nivel de acceso del usuario."""
        pass

    @abstractmethod
    def get_by_id(self, document_id: int) -> Optional[DocumentEntity]:
        pass

    @abstractmethod
    def save_new_version(self, document_id: int, file_path: str, user_id: int, summary: str) -> bool:
        """Guarda una nueva versión y actualiza el archivo principal."""
        pass