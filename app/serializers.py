from pydantic import BaseModel
from typing import List, Optional
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



class HospitalBatchResponse(BaseModel):
    batch_id: str
    hospitals: List[HospitalResponse]


class HospitalResult(BaseModel):
    row: int
    hospital_id: Optional[int]
    name: str
    status: str


class BulkResponse(BaseModel):
    batch_id: str
    total_hospitals: int
    processed_hospitals: int
    failed_hospitals: int
    processing_time_seconds: float
    activated: bool
    hospitals: List[HospitalResult]
