from dataclasses import dataclass, field
from typing import Optional, List

@dataclass
class UserEntity:
    id: Optional[int]
    dni: str
    role: str
    first_name: str
    last_name: str
    password_changed: bool
    is_active: bool
    support_role: Optional[str] = None
    module_permissions: List[str] = field(default_factory=list)