import logging

from celery import shared_task
from celery.signals import worker_ready

from apps.notifications.constants import (
    MAX_RETRIES,
    RETRY_PUSH_TIME,
    NotificationTypes,
)
from apps.notifications.models import Device, NotificationsBase
from apps.notifications.push_service import PushService
from apps.notifications.utils import delete_old_devices

logger = logging.getLogger('django.notifications')


@shared_task
def init_push_service():
    """
    Initialize the push service to ensure Firebase Admin SDK is set up.
    """
    try:
        push_service = PushService()
        if not push_service.enable:
            logger.error('Push service is not enabled. Check configuration.')
            return False
        logger.info('Push service initialized successfully.')
        return True
    except Exception as e:
        logger.error(
            f'Error initializing push service: {str(e)}', exc_info=True
        )
        return False


@shared_task(bind=True)
def send_push_notifications_on_upcoming_events(
    self,
    event_id,
    notification_type
):
    """
    Send notifications about a specific event.
    """
    try:
        push_service = PushService()
        logger.info(
            f'Executing task: send_event_notification for event {event_id}, '
            f'type: {notification_type}'
        )

        result = push_service.process_notifications_by_type(
            type=notification_type,
            event_id=event_id,
        )

        if result['status']:
            logger.info(
                f'Successfully sent notifications for event {event_id}'
            )
        else:
            logger.warning(f'No notifications sent for event {event_id}')
        return result
    except Exception as e:
        logger.error(
            f'Error sending notification for event {event_id}: {str(e)}',
            exc_info=True,
        )
        self.retry(exc=e, countdown=RETRY_PUSH_TIME, max_retries=MAX_RETRIES)
        return {'status': False, 'message': str(e)}


@shared_task(bind=True)
def retry_notification_task(self, token, notification_type, event_id=None):
    """
    Retry sending notification to a specific token.

    Args:
        token: Device token to retry
        notification_type: Type of notification
        event_id: Game ID if applicable
    """
    try:
        logger.info(f'Retrying notification to token {token[:8]}...')
        notification = NotificationsBase.objects.get(
            type=notification_type
        )
        push_service = PushService()
        device = Device.objects.filter(token=token).first()
        result = push_service.send_notification_by_device(
            device=device, notification=notification, event_id=event_id
        )
        if result:
            logger.info(f'Retry successful for token {token[:8]}...')
        else:
            logger.warning(f'Retry failed for token {token[:8]}...')
        return result
    except Exception as e:
        logger.error(f'Error in retry task: {str(e)}', exc_info=True)
        self.retry(
            exc=e, countdown=RETRY_PUSH_TIME, max_retries=MAX_RETRIES - 1
        )

@shared_task(bind=True)
def inform_removed_players(event_id: int, player_id: int, event_type: str):
    """
    Inform players that they have been removed from an event.
    """
    notification_type = {
        'game': NotificationTypes.GAME_REMOVED,
        'tourney': NotificationTypes.TOURNEY_REMOVED
    }.get(event_type)
    if not notification_type:
        logger.error(f'Invalid event type: {event_type}')
        return False
    push_service = PushService()
    if not push_service:
        logger.error('Push service is not enabled. Check configuration.')
        return False
    return push_service.process_notifications_by_type(
        notification_type=notification_type,
        player_id=player_id,
        event_id=event_id
    )


@shared_task
def delete_old_devices_task():
    """
    Delete device records created more than 270 days ago.
    """
    return delete_old_devices()


@shared_task
def create_notification_type_tables():
    """
    Create initial notification types in the database if they do not exist.
    """
    try:
        NotificationsBase.create_db_model_types()
        logger.info('Notification types initialized successfully.')
        return True
    except Exception as e:
        logger.error(
            f'Error initializing notification types: {str(e)}', exc_info=True
        )
        return False

@worker_ready.connect
def at_start(**kwargs):
    """Start the push service initialization task when the worker is ready."""
    init_push_service.apply_async()
    create_notification_type_tables.apply_async()