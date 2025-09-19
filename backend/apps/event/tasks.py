import logging

from celery import shared_task

from apps.notifications.constants import MAX_RETRIES, RETRY_PUSH_TIME
from apps.notifications.push_service import PushService

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=MAX_RETRIES,
    default_retry_delay=RETRY_PUSH_TIME
)
def send_event_notification_task(self, event_id: int, notification_type: str):
    """
    Sends notification to users about an upcoming event (Game or Tourney).
    notification_type: 'InGame' or 'InTourney'
    """
    push_service = PushService()
    if not push_service:
        push_service.reconnect()
        if not push_service:
            logger.error("Push service is not available")
            return {
                'status': False,
                'message': 'Push service is not available'
            }
    return push_service.process_notifications_by_type(
        event_id, notification_type
    )
