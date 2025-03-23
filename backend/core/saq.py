import logging
from functools import cache
from saq import Queue

from .config import settings

@cache
def get_saq_queue() -> Queue | None:
    try:
        if not settings.REDIS_URL:
            logging.error("SAQ disabled due to REDIS_URL not set")
            return None
        
        logging.info(f"Initializing SAQ with REDIS_URL: {settings.REDIS_URL}")
        queue = Queue.from_url(settings.REDIS_URL)
        logging.info("SAQ queue initiated successfully")
        return queue
    except Exception as e:
        logging.error(f"Failed to initiate SAQ queue: {e}")
        return None 