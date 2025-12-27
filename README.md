# Hospital Management System ✅

A small FastAPI service to manage hospitals and bulk hospital imports using CSV files. It supports single hospital CRUD, bulk CSV upload with background processing (Celery + Redis), batch tracking, validation, and batch activation.

---

## Table of Contents

- [Features](#features)
- [Endpoints](#endpoints)
- [CSV format](#csv-format)
- [Setup - Local Development](#setup---local-development)
- [Setup - Production](#setup---production)
- [Running the worker (Celery)](#running-the-worker-celery)
- [Database migrations](#database-migrations)
- [Testing](#testing)
- [Contributing](#contributing)
- [Notes & Tips](#notes--tips)

---

## Features 🔧

- Create and list hospitals
- Get a hospital by ID
- Upload hospital CSVs for background processing
- Validate CSVs before uploading
- Track batch processing status and results
- Activate or delete batches

---

## Endpoints 📡

Base URL: `http://localhost:8000`

1) Create a hospital

- POST `/hospitals`
- Body (JSON):

```json
{
  "name": "Hospital A",
  "address": "123 Main St",
  "phone": "123-456-7890",
  "is_active": false
}
```
- Response: `201 Created` with hospital data (see `HospitalResponse` model)


2) List hospitals

- GET `/hospitals`
- Response: `200 OK` list of hospitals

3) Get a hospital by id

- GET `/hospitals/{hospital_id}`
- Response: `200 OK` with hospital or `404` if not found

4) Upload CSV for bulk creation (async)

- POST `/hospitals/bulk`
- Form body: file field named `file` (CSV file) — max 20 rows
- Response: `201 Created` with JSON:

```json
{
  "batch_id": "<uuid>",
  "status": "IN_PROGRESS",
  "total_hospitals": 5,
  "message": "Bulk processing started. Use batch_id to track progress."
}
```

After upload, a background Celery task processes the CSV and updates a `JobStatus` record.

5) Validate CSV (no DB write)

- POST `/hospitals/bulk/validate`
- Form body: file field named `file` (CSV file)
- Response: `200 OK` with `message: "CSV is valid"` and `total_rows` on success
- Returns `400` with validation errors on failure

6) Get batch status and results

- GET `/hospitals/batch/{batch_id}`
- Response includes: `batch_id`, `total_hospitals`, `processed_hospitals`, `failed_hospitals`, `processing_time_seconds`, `sys_custom_fields`, `hospitals` (created rows)

7) Activate batch (flip all its hospitals to active)

- PATCH `/hospitals/batch/{batch_id}/activate`
- Returns batch summary and `batch_activated` flag

8) Delete a batch (remove hospitals in batch and job status)

- DELETE `/hospitals/batch/{batch_id}`
- Response: `204 No Content`

---

## CSV format 📄

- Required columns: `name`, `address`
- Optional columns: `phone`
- Maximum rows: **20**
- Example CSV (header + rows):

```
name,address,phone
Hospital A,123 Main St,123-456
Hospital B,456 Broadway,987-654
```

Validation checks ensure required columns exist, no unexpected columns, and that each row has `name` and `address`.

---

## Setup - Local Development 🧰

Prerequisites:

- Python 3.12+
- Docker & Docker Compose (recommended)
- Redis and PostgreSQL (can be started with Docker Compose)

Quick start using Docker Compose:

```bash
# start postgres + redis
docker-compose up -d

# create DB and run migrations (see section below)
alembic upgrade head

# install dependencies (optional if using Docker)
# install dependencies using the `uv` package manager
uv install

# run the app
python run.py
# or
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Example environment variables (.env):

```
DATABASE_URL=postgresql+asyncpg://QA_Test:QA_Test@postgres:5432/HMS
REDIS_URL=redis://redis:6379/0
```

> Note: the repository uses `DATABASE_URL` with a default pointing to `postgresql+asyncpg://QA_Test:QA_Test@localhost:5432/HMS` if not provided.

---

## Setup - Production 🚀

Recommendations for production deploy:

- Use a process manager (systemd) or container orchestration (Docker Swarm, Kubernetes)
- Use Gunicorn with Uvicorn workers for robust deployments:

```bash
gunicorn -k uvicorn.workers.UvicornWorker app.main:app -w 4 -b 0.0.0.0:8000
```

- Use a hosted Redis or Redis cluster for Celery broker/backend
- Set environment variables for `DATABASE_URL` and Celery broker/backend
- Run migrations with `alembic upgrade head` as part of your CI/CD
- Use healthchecks and monitoring for Celery and the app

---

## Running the worker (Celery) 🐝

Start a worker to process uploaded CSVs:

```bash
# local (requires redis running)
celery -A worker.celery.celery_app worker --loglevel=info
```

If using Docker Compose, ensure the worker service can connect to the same Redis instance.

---

## Database migrations 🗄️

Migrations are handled with Alembic. Basic commands:

```bash
# generate a new migration
alembic revision --autogenerate -m "Add feature"

# apply migrations
alembic upgrade head
```

Check `alembic/versions` for the existing migration files.

---

## Testing ✅

Tests use `pytest` and `pytest-asyncio`. To run tests locally:

```bash
# install dependencies using the `uv` package manager (includes test deps)
uv install
pytest -q
```

There is also a `docker-compose.test.yml` to spin up test dependencies if needed:

```bash
docker-compose -p hms_test -f docker-compose.test.yml up -d
```

---

## Contributing 🤝

- Open an issue for bugs or feature requests
- Write clear, focused PRs with tests for changes
- Keep changes small and descriptive

---

## Notes & Tips 💡

- CSV uploads are limited to 20 rows to keep background processing small and predictable.
- The Celery task `worker.tasks.process_bulk_hospitals` will update `JobStatus` rows with `processed_hospitals`, `failed_hospitals`, and `sys_custom_fields` which contain per-row errors when present.
- If you want Celery to use a configurable broker/backed, update `worker/celery.py` to read `BROKER_URL`/`BACKEND_URL` from environment variables instead of the hard-coded Redis URLs.

---

If you'd like, I can also:

- Add example curl/httpie commands or Postman collection
- Add a quick `docker-compose` service to run the web app and worker together

---

**Happy hacking!**
