import logging
from functools import cache

from celery import Celery

from core.config import settings


@cache
def get_celery_app() -> Celery | None:
    try:
        if settings.CELERY_BROKER_URL is None:
            logging.error(f"CELERY disabled due to CELERY_BROKER_URL not set")
            return None

        if settings.CELERY_BACKEND_URL is None:
            logging.error(f"CELERY disabled due to CELERY_BACKEND_URL not set")
            return None

        celery_app = Celery(broker=settings.CELERY_BROKER_URL, backend=settings.CELERY_BACKEND_URL, task_default_queue=settings.CELERY_DEFAULT_QUEUE,
                            include=["app.worker.celery.tasks"])
        logging.info("Celery initiated")
        return celery_app
    except Exception as e:
        logging.error(f"Failed to initiate celery app: {e}")
        return None
