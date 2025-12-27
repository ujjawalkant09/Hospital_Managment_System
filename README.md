# Hospital_Managment_System

Run docker-compose up -d

Run docker
export PYTHONPATH=.
uv run celery -A worker.celery.celery_app worker --loglevel=info


Run FastAPI server 

uv run python run.py


