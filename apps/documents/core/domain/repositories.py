from abc import ABC, abstractmethod
from typing import List, Optional
from .entities import DocumentEntity, DocumentCategoryEntity

class IDocumentRepository(ABC):
    @abstractmethod
    def get_all_accessible(self, user_role: str) -> List[DocumentEntity]: pass

    @abstractmethod
    def get_by_id(self, document_id: int) -> Optional[DocumentEntity]: pass

    @abstractmethod
    def save_new_version(self, document_id: int, file_path: str, user_id: int, summary: str) -> bool: pass

    @abstractmethod
    def save(self, document: DocumentEntity) -> DocumentEntity: pass

    # --- NUEVAS FUNCIONES PARA DOCUMENTOS ---
    @abstractmethod
    def update_document(self, document_id: int, title: str, category_id: int, access_level: str, tags: str, file_path: Optional[str] = None) -> DocumentEntity: pass

    @abstractmethod
    def delete_document(self, document_id: int) -> bool: pass

    # --- GESTIÓN DE CATEGORÍAS ---
    @abstractmethod
    def get_all_categories(self) -> List[DocumentCategoryEntity]: pass

    @abstractmethod
    def create_category(self, name: str) -> DocumentCategoryEntity: pass

    @abstractmethod
    def update_category(self, category_id: int, new_name: str) -> DocumentCategoryEntity: pass

    @abstractmethod
    def delete_category(self, category_id: int) -> bool: pass