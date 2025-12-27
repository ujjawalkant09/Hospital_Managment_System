from fastapi import FastAPI, UploadFile, File, HTTPException,Depends
from uuid import uuid4
import csv
import io
import time
from .database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from .serializers import (
    HospitalCreate,
    HospitalResponse,
    HospitalBatchResponse,
    BulkResponse,
    HospitalResult,
)
from models import Hospital, JobStatus
from sqlalchemy import select, update, delete

app = FastAPI()


@app.post("/hospitals", response_model=HospitalResponse, status_code=201)
async def create_hospital(payload: HospitalCreate, db: AsyncSession = Depends(get_db)):
   hospital = Hospital(
        name=payload.name,
        address=payload.address,
        phone=payload.phone,    
        creation_batch_id=None,
        is_active=payload.is_active,
    )
   db.add(hospital)
   await db.commit()
   await db.refresh(hospital)
   return hospital


@app.get("/hospitals")
async def list_hospitals( db: AsyncSession = Depends(get_db),):
    result = await db.execute(select(Hospital))
    hospitals = result.scalars().all()
    return hospitals

@app.get("/hospitals/{hospital_id}", response_model=HospitalResponse)
async def get_hospital(
    hospital_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Hospital).where(Hospital.id == hospital_id)
    )
    hospital = result.scalar_one_or_none()

    if hospital is None:
        raise HTTPException(status_code=404, detail="Hospital not found")

    return hospital



@app.get("/hospitals/batch/{batch_id}",response_model=HospitalBatchResponse,)
async def get_hospital_batch(
    batch_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(JobStatus).where(JobStatus.batch_id == batch_id)
    )
    job = result.scalar_one_or_none()

    if job is None:
        raise HTTPException(status_code=404, detail="Batch not found")

    result = await db.execute(
        select(Hospital).where(Hospital.creation_batch_id == batch_id)
    )
    hospitals = result.scalars().all()

    return {
        "batch_id": batch_id,
        "hospitals": hospitals,
    }



@app.patch("/hospitals/batch/{batch_id}/activate")
async def activate_batch(
    batch_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(JobStatus).where(JobStatus.batch_id == batch_id)
    )
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=404, detail="Batch not found")
    await db.execute(
        update(Hospital)
        .where(Hospital.creation_batch_id == batch_id)
        .values(is_active=True)
    )

    await db.commit()
    return {
        "batch_id": batch_id,
        "status": "activated",
    }





@app.delete("/hospitals/batch/{batch_id}", status_code=204)
async def delete_batch( batch_id: str, db: AsyncSession = Depends(get_db),):

    result = await db.execute(
        select(JobStatus).where(JobStatus.batch_id == batch_id)
    )
    job = result.scalar_one_or_none()

    if job is None:
        raise HTTPException(status_code=404, detail="Batch not found")

    await db.execute(
        delete(Hospital).where(Hospital.creation_batch_id == batch_id)
    )

    await db.delete(job)

    await db.commit()



@app.post("/hospitals/bulk", status_code=201)
async def create_hospitals_bulk(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")

    content = await file.read()
    csv_text = content.decode("utf-8")

    reader = csv.DictReader(io.StringIO(csv_text))
    rows = list(reader)

    if not rows:
        raise HTTPException(status_code=400, detail="Empty CSV")

    if len(rows) > 20:
        raise HTTPException(status_code=400, detail="Max 20 hospitals allowed")

    batch_id = str(uuid4())
    job = JobStatus(
        batch_id=batch_id,
        total_hospitals=len(rows),
        processed_hospitals=0,
        failed_hospitals=0,
        status="IN_PROGRESS",
        sys_custom_fields={},  
    )

    db.add(job)
    await db.commit()

    from worker.tasks import process_bulk_hospitals
    process_bulk_hospitals.delay(batch_id, csv_text)

    return {
        "batch_id": batch_id,
        "status": "IN_PROGRESS",
        "total_hospitals": len(rows),
        "message": "Bulk processing started. Use batch_id to track progress."
    }