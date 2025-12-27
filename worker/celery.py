# celery_worker.py
from celery import Celery
from dotenv import load_dotenv
import os
load_dotenv() 

broker = os.getenv("CELERY_BROKER_URL")
backend = os.getenv("CELERY_RESULT_BACKEND")


celery_app = Celery(
    "celery",
    broker=broker,
    backend=backend,
)


celery_app.autodiscover_tasks(["worker"])
