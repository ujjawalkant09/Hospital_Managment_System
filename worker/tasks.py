import csv
import io
import time
import asyncio
from worker.celery import celery_app
from app.database import async_session_factory
from models import Hospital, JobStatus
from sqlalchemy import select


@celery_app.task(
    bind=True,
    name="bulk_hospitals_task",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 5},
)
def process_bulk_hospitals(self, batch_id: str, csv_text: str) -> None:

    async def _run():
        start_time = time.time()

        async with async_session_factory() as db:
            result = await db.execute(
                select(JobStatus).where(JobStatus.batch_id == batch_id)
            )
            job = result.scalar_one_or_none()
            if not job:
                return
            
            reader = csv.DictReader(io.StringIO(csv_text))
            processed = 0
            failed = 0
            job.sys_custom_fields.setdefault("hospitals", {})

            for idx, row in enumerate(reader, start=1):
                error_info = None
                name = row.get("name")
                address = row.get("address")
                hospital_key = name or f"row_{idx}"
                try:
                    if not name or not address:
                        failed += 1
                        job.sys_custom_fields["hospitals"][hospital_key] = {
                            "error": (
                                f"Missing required fields. "
                                f"Name: {name}, Address: {address}"
                            )
                        }
                        continue
                    hospital = Hospital(
                        name=name,
                        address=address,
                        phone=row.get("phone"),
                        creation_batch_id=batch_id,
                        is_active=False,
                    )
                    db.add(hospital)
                    await db.flush()
                    processed += 1

                except Exception as err:
                    failed += 1
                    error_info = str(err)

                if error_info:
                    job.sys_custom_fields["hospitals"][hospital_key] = {
                        "error": error_info
                    }

                job.processed_hospitals = processed
                job.failed_hospitals = failed

            job.status = (
                "COMPLETED" if failed == 0 else "COMPLETED_WITH_ERRORS"
            )
            job.processing_time_seconds = round(
                time.time() - start_time, 2
            )

            await db.commit()

    asyncio.run(_run())