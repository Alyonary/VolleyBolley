import logging

from celery import shared_task
from django.utils import timezone

from apps.event.models import Game, Tourney
from apps.event.utils import create_event_rate_objects_and_notify

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def create_rate_objects_and_notify(self):
    """
    Create PlayerEventRate objects for players in past events
    and notify them to rate the event if they haven't already.
    This task should be run periodically (every 10 min) to check for events
    """
    try:
        hour_ago = timezone.now() - timezone.timedelta(hours=1)
        create_event_rate_objects_and_notify(Game, hour_ago)
        logger.info("Successfully created PlayerEventRate objects")
        create_event_rate_objects_and_notify(Tourney, hour_ago)
    except Exception as e:
        logger.error(f"Error creating PlayerEventRate objects: {e}")
        raise self.retry(exc=e) from e