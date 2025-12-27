from pydantic import BaseModel
from typing import Optional
from datetime import datetime



class HospitalCreate(BaseModel):
    name: str
    address: str
    phone: Optional[str] = None
    is_active: bool = False



class HospitalResponse(BaseModel):
    id: int
    name: str
    address: str
    phone: Optional[str]
    creation_batch_id: Optional[str]
    is_active: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
