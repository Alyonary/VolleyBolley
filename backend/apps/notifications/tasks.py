import logging
from datetime import datetime, timedelta

from celery import shared_task
from celery.signals import worker_ready
from django.utils import timezone

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


@shared_task(
    bind=True, max_retries=MAX_RETRIES, default_retry_delay=RETRY_PUSH_TIME
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
            logger.error('Push service is not available')
            return {
                'status': False,
                'message': 'Push service is not available',
            }

    return push_service.process_notifications_by_type(
        notification_type, event_id
    )


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
        notification = NotificationsBase.objects.get(type=notification_type)
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
def inform_removed_players_task(
    self, event_id: int, player_id: int, event_type: str
):
    """
    Inform players that they have been removed from an event.
    """
    notification_type = {
        'game': NotificationTypes.GAME_REMOVED,
        'tourney': NotificationTypes.TOURNEY_REMOVED,
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
        event_id=event_id,
    )


def procces_rate_notifications_for_recent_events():
    """
    Find all games and tourneys ended an hour ago and send rate notifications.
    """
    from apps.event.models import Game, Tourney

    hour_ago = timezone.now() - timedelta(hours=1)
    send_rate_notification_for_events(Game, hour_ago)
    send_rate_notification_for_events(Tourney, hour_ago)


def send_rate_notification_for_events(
    event_type: type, hour_ago: datetime
) -> bool:
    """
    Sends notification to all players in the event to rate other players.
    """
    from apps.event.models import Game

    events = event_type.objects.filter(
        end_time__gte=hour_ago, end_time__lt=timezone.now()
    )
    if issubclass(event_type, Game):
        notification_type = NotificationTypes.GAME_RATE
    else:
        notification_type = NotificationTypes.TOURNEY_RATE

    for event in events:
        send_event_notification_task.delay(event.id, notification_type)
        event.is_active = False
        event.save()
    logger.info(
        f'Processed {events.count()} {event_type.__name__} '
        f'events for rate notifications.'
    )
    return True


@shared_task
def send_rate_notification_task():
    """Wrapper task for scheduled rate notifications."""
    return procces_rate_notifications_for_recent_events()


@shared_task
def delete_old_devices_task():
    """
    Delete device records created more than 270 days ago.
    """
    return delete_old_devices()


@shared_task
def create_notification_type_tables_task():
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
    create_notification_type_tables_task.apply_async()
