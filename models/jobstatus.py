from sqlalchemy import Column, Integer, String, DateTime, text, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict
from app.database import Base


class JobStatus(Base):
    __tablename__ = "job_status"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(String(36), unique=True, index=True, nullable=False)
    total_hospitals = Column(Integer, nullable=False)
    processed_hospitals = Column(Integer, default=0)
    failed_hospitals = Column(Integer, default=0)
    status = Column(String(50), default="IN_PROGRESS")
    processing_time_seconds = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    sys_custom_fields = Column( MutableDict.as_mutable(JSONB), nullable=False, default=dict,server_default=text("'{}'::jsonb") 
)


    hospitals = relationship(
                "Hospital",
                primaryjoin="JobStatus.batch_id == Hospital.creation_batch_id",
                viewonly=True,
            )

