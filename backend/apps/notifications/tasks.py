import logging
from datetime import datetime

from celery import shared_task
from celery.signals import worker_ready
from django.utils import timezone

from apps.notifications.constants import (
    MAX_RETRIES,
    RETRY_PUSH_TIME,
    NotificationTypes,
)
from apps.notifications.models import (
    NotificationsBase,
    NotificationsTime,
)
from apps.notifications.push_service import PushService
from apps.notifications.task_manager import TaskManager
from apps.notifications.utils import delete_old_devices

logger = logging.getLogger('django.notifications')


@shared_task
def send_invite_to_player_task(
    player_id: int, event_id: int, notification_type: str
):
    """
    Sends an invitation notification to a player for a Game or Tourney.
    """
    push_service = PushService()
    return push_service.send_to_player(
        player_id=player_id,
        notification_type=notification_type,
        event_id=event_id,
    )


@shared_task
def send_notification_to_player_task(
    player_id: int, event_id: int, notification_type: str
):
    """Sends notification to the player."""
    push_service = PushService()
    return push_service.send_to_player(
        player_id=player_id,
        notification_type=notification_type,
        event_id=event_id,
    )


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
    return push_service.send_push_for_event(notification_type, event_id)


@shared_task(bind=True)
def retry_notification_task(
    self, player_id: int, notification_type: str, event_id=None
):
    """
    Retry sending notification to a specific player.
    """
    try:
        push_service = PushService()
        result = push_service.send_to_player(
            player_id=player_id,
            notification_type=notification_type,
            event_id=event_id,
        )
        if result.get('status', False):
            logger.info(f'Retry successful for player ID {player_id}')
        else:
            logger.warning(f'Retry failed for player ID {player_id}')
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
    Inform player that have been removed from an event.
    """
    notification_type = {
        'game': NotificationTypes.GAME_REMOVED,
        'tourney': NotificationTypes.TOURNEY_REMOVED,
    }.get(event_type)
    push_service = PushService()
    return push_service.send_to_player(
        notification_type=notification_type,
        player_id=player_id,
        event_id=event_id,
    )


@shared_task
def send_rate_game_notification_task():
    """
    Find all games ended a specific time ago.
    Send rate notifications.
    """
    from apps.event.models import Game

    closed_event_time = (
        timezone.now() - NotificationsTime.get_closed_event_notification_time()
    )
    send_rate_notification_for_events(Game, closed_event_time)


@shared_task
def send_rate_tourney_notification_task():
    """
    Find all tourneys ended a specific time ago.
    Send rate notifications.
    """
    from apps.event.models import Tourney

    closed_event_time = (
        timezone.now() - NotificationsTime.get_closed_event_notification_time()
    )
    send_rate_notification_for_events(Tourney, closed_event_time)


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
    init_push_service.apply_async()
    create_notification_type_tables_task.apply_async()


# =========================
# Internal task implementations
# =========================


def send_rate_notification_for_events(
    event_type: type, closed_event_time: datetime
) -> bool:
    """
    Sends notification to all players in the event to rate other players.
    """
    from apps.event.models import Game

    events = event_type.objects.filter(
        end_time__gte=closed_event_time, end_time__lt=timezone.now()
    )
    if issubclass(event_type, Game):
        notification_type = NotificationTypes.GAME_RATE
    else:
        notification_type = NotificationTypes.TOURNEY_RATE
    for event in events:
        task_manager = TaskManager()
        task_manager.create_task(
            send_event_notification_task,
            eta=None,
            event_id=event.id,
            notification_type=notification_type,
        )
        event.is_active = False
        event.save()
    logger.info(
        f'Processed {events.count()} {event_type.__name__} '
        f'events for rate notifications.'
    )
    return True
