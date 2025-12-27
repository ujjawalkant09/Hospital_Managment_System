import io
import pytest
from httpx import AsyncClient, ASGITransport
from models import Hospital, JobStatus

from app.main import app


def get_client():
    return AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    )


@pytest.mark.asyncio
async def test_create_hospital(override_get_db):
    async with get_client() as ac:
        payload = {
            "name": "Test Hospital",
            "address": "123 Test St",
            "phone": "111222333",
            "is_active": True,
        }
        r = await ac.post("/hospitals", json=payload)
        assert r.status_code == 201


@pytest.mark.asyncio
async def test_list_hospitals(override_get_db):
    async with get_client() as ac:
        r = await ac.get("/hospitals")
        assert r.status_code == 200


@pytest.mark.asyncio
async def test_get_hospital_found_and_not_found(override_get_db):
    async with get_client() as ac:
        create = await ac.post(
            "/hospitals",
            json={"name": "X", "address": "Addr X"},
        )
        hospital_id = create.json()["id"]

        r = await ac.get(f"/hospitals/{hospital_id}")
        assert r.status_code == 200

        r = await ac.get("/hospitals/999999")
        assert r.status_code == 404


@pytest.mark.asyncio
async def test_get_hospital_batch_found(override_get_db):
    db = override_get_db  

    job = JobStatus(
        batch_id="batch-1",
        total_hospitals=1,
        processed_hospitals=1,
        failed_hospitals=0,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    hospital = Hospital(
        name="Test Hospital",
        address="Addr",
        creation_batch_id="batch-1",
        is_active=False,
    )
    db.add(hospital)
    await db.commit()

    async with get_client() as ac:
        r = await ac.get("/hospitals/batch/batch-1")

    assert r.status_code == 200
    data = r.json()
    assert data["batch_id"] == "batch-1"
    assert len(data["hospitals"]) == 1



@pytest.mark.asyncio
async def test_activate_and_delete_batch(override_get_db):
    async with get_client() as ac:
        r = await ac.patch("/hospitals/batch/b-1/activate")
        assert r.status_code in (200, 404)

        r = await ac.delete("/hospitals/batch/b-1")
        assert r.status_code in (204, 404)


@pytest.mark.asyncio
async def test_bulk_create_success(override_get_db, monkeypatch):
    monkeypatch.setattr(
        "worker.tasks.process_bulk_hospitals.delay",
        lambda *args, **kwargs: None,
    )

    csv_content = b"""name,address,phone
A,Addr A,1
B,Addr B,2
"""

    files = {"file": ("hospitals.csv", io.BytesIO(csv_content), "text/csv")}

    async with get_client() as ac:
        r = await ac.post("/hospitals/bulk", files=files)
        assert r.status_code == 201
        assert r.json()["status"] == "IN_PROGRESS"


@pytest.mark.asyncio
async def test_bulk_create_errors(override_get_db):
    async with get_client() as ac:
        files = {"file": ("bad.txt", io.BytesIO(b"x,y"), "text/plain")}
        r = await ac.post("/hospitals/bulk", files=files)
        assert r.status_code == 400
