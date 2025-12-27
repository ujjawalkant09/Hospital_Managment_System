from pydantic import BaseModel,ConfigDict
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
    phone: Optional[str] = None
    creation_batch_id: Optional[str] = None
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
