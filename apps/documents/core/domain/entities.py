from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime

@dataclass
class DocumentCategoryEntity:
    id: Optional[int]
    name: str
    description: Optional[str] = None

@dataclass
class DocumentVersionEntity:
    id: Optional[int]
    document_id: int
    file_path: str
    version_number: int
    uploaded_by_name: str
    created_at: Optional[datetime] = None
    change_summary: Optional[str] = None

@dataclass
class DocumentEntity:
    id: Optional[int]
    title: str
    category_name: str
    category_id: int
    access_level: str
    tags: str
    current_file_path: str
    uploaded_by_name: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    versions: List[DocumentVersionEntity] = field(default_factory=list)