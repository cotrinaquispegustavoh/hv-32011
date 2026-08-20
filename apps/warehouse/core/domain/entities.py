from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime

@dataclass
class MaterialEntity:
    id: Optional[int]
    name: str
    category: str
    stock: int
    unit: str
    state: str
    location: str
    cycle: str
    pedagogical_use: Optional[str]
    main_image_url: Optional[str] = None
    new_image_path: Optional[str] = None

@dataclass
class LoanDetailEntity:
    id: Optional[int]
    material_id: int
    quantity_requested: int
    quantity_returned: int
    quantity_waste: int
    material_name: Optional[str] = None 
    material_unit: Optional[str] = None 

@dataclass
class LoanRequestEntity:
    id: Optional[int]
    teacher_id: int
    request_date: Optional[datetime]
    status: str
    details: List[LoanDetailEntity]
    required_for: Optional[datetime] = None
    expected_return_date: Optional[datetime] = None
    teacher_name: Optional[str] = None