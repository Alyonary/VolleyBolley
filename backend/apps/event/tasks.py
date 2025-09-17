import logging

from celery import shared_task

from apps.event.utils import procces_rate_notifications_for_recent_events

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def create_rate_objects_and_notify(self):
    """
    Create PlayerEventRate objects for players in past events
    and notify them to rate the event if they haven't already.
    This task should be run periodically (every 10 min) to check for events
    """
    try:
        procces_rate_notifications_for_recent_events()
        logger.info("Successfully created PlayerEventRate objects")
    except Exception as e:
        logger.error(f"Error creating PlayerEventRate objects: {e}")
        raise self.retry(exc=e) from e
    

@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def send_event_notification_task(self, event_id: int, notification_type: str):
    """
    Sends notification to users about an upcoming event (Game or Tourney).
    notification_type: 'InGame' or 'InTourney'
    """
    ###доработаю после мержа пуш сервиса
    logger.info(
        f"Notification sent for event {event_id} of type {notification_type}"
    )
    return True
    