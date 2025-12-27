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

**Overview:** Run the app and its dependencies locally using Docker Compose (recommended) or directly on your host for quick iteration.

### Prerequisites

- Python 3.12+ (for local development without Docker)
- Docker & Docker Compose (recommended)
- `uv` package manager or pip for dependency installation

### Option A — Recommended: Using Docker Compose

1. Create a `.env` file in the project root (example below) and make any necessary overrides.

2. Start the dependencies:

```bash
# Start Postgres + Redis
docker-compose up -d
```

3. Build/run the app and worker (example dev compose snippet below — add to `docker-compose.override.yml` or your dev compose file):

```yaml
version: '3.8'
services:
  web:
    build: .
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - postgres
      - redis

  worker:
    build: .
    command: celery -A worker.celery.celery_app worker --loglevel=info
    env_file:
      - .env
    depends_on:
      - redis
      - postgres
```

4. Run database migrations:

```bash
# When web service exists in your compose setup
docker-compose run --rm web alembic upgrade head
# or (if web is already running)
docker-compose exec web alembic upgrade head
```

5. Visit the app at: `http://localhost:8000`

### Option B — Run without Docker (host machine)

1. Create and activate a virtual environment
2. Install dependencies with `uv install` (or `pip install -r requirements.txt`)
3. Set environment variables locally (see example `.env` below)
4. Start Postgres/Redis (e.g., via Docker), run migrations, then:

```bash
python run.py
# or
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Example `.env` (development)

```
DATABASE_URL=postgresql+asyncpg://{DATABASE_URL}
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1
```

> Tip: If you run a DB on your host, update `DATABASE_URL` to use `localhost` (e.g., `postgresql+asyncpg://QA_Test:QA_Test@localhost:5432/HMS`).

### Tests

Use the provided test compose file for DB integration tests:

```bash
docker-compose -p hms_test -f docker-compose.test.yml up -d
pytest -q
```

### Troubleshooting

- If you see DB connection errors, verify `DATABASE_URL` and that the `postgres` service is healthy: `docker-compose logs -f postgres`.
- For migration issues: double-check alembic config, and run `alembic revision --autogenerate` and `alembic upgrade head`.
- Use `docker-compose logs -f web` or `docker-compose logs -f worker` to inspect application and Celery logs.

---


## Setup - Production 🚀

**Goal:** Provide reliable, secure, and scalable deployment for the app and background workers.

### Recommended runtime

- Container Docker Compose with a process supervisor is recommended for production.
- Use a managed/Postgres (RDS, Cloud SQL) and a managed Redis instance where possible for reliability.

### Production Docker Compose (example)

Create a production compose file (e.g., `docker-compose.prod.yml`) that uses pre-built images and environment secrets rather than mounting source code:

```yaml
version: '3.8'
services:
  web:
    image: <your-registry>/hms:latest
    command: gunicorn -k uvicorn.workers.UvicornWorker app.main:app -w 4 -b 0.0.0.0:8000
    ports:
      - "8000:8000"
    env_file:
      - .env.prod
    depends_on:
      - postgres
      - redis

  worker:
    image: <your-registry>/hms:latest
    command: celery -A worker.celery.celery_app worker --loglevel=info
    env_file:
      - .env.prod
    depends_on:
      - redis
      - postgres
```

### Building and migrating

1. Build and push images in CI (tagged with commit SHA).
2. In deploy pipeline, run migrations before switching traffic:

```bash
# Run against the running web container or as a one-off job
docker-compose -f docker-compose.prod.yml run --rm web alembic upgrade head
```

### Deploy scripts (optional helpers)

This repo includes two lightweight helper scripts to simplify deploy/start and stop operations when using the included `docker-compose.yml`:

- `deploy.sh` — builds and starts services using Docker Compose. It expects an `.env.docker` file in the repository root (used as an env file) and runs `docker compose -f docker-compose.yml -p hospital_management_system up -d` after building images.
- `stop.sh` — stops and removes the project containers using `docker compose -f docker-compose.yml -p hospital_management_system down`.

Quick usage:

```bash
# Make scripts executable (first time)
chmod +x deploy.sh stop.sh

# Deploy / start services (requires .env.docker to exist)
./deploy.sh

# Stop services
./stop.sh
```

Example `.env.docker` (place in project root):

```
# .env.docker (example)
DATABASE_URL=postgresql+asyncpg://<user>:<password>@<host>:<port>/<db>
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1
```

Notes:

- `deploy.sh` validates that Docker and Docker Compose v2 are available and that `.env.docker` exists before proceeding.
- The scripts use the compose project name `hospital_management_system`; if you need a different project name, either modify the scripts or run Docker Compose directly with your preferred `-p` value.

### Security & best practices

- **Do not** expose Postgres or Redis to the public internet. Use internal networking or VPC peering.
- Use environment variables or secrets managers (Vault, Kubernetes secrets, AWS SSM) for credentials.
- Monitor Celery and the web app with metrics and logs (Prometheus/Grafana, ELK, or a logging provider).
- Set resource limits for containers and autoscaling rules for workers.

### Healthchecks & zero-downtime

- Use liveness/readiness probes (Kubernetes) or health checks in your orchestrator.
- Use rolling deployments or blue-green strategies for zero-downtime deploys.

---



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


## Notes & Tips 💡

- CSV uploads are limited to 20 rows.
- The Celery task `worker.tasks.process_bulk_hospitals` will update `JobStatus` rows with `processed_hospitals`, `failed_hospitals`, and `sys_custom_fields` which contain per-row errors when present.
- If you want Celery to use a configurable broker/backed, update `worker/celery.py` to read `BROKER_URL`/`BACKEND_URL` from environment variables instead of the hard-coded Redis URLs.

