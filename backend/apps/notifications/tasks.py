import logging

from celery import shared_task

from apps.notifications.constants import (
    MAX_RETRIES,
    RETRY_PUSH_TIME,
)
from apps.notifications.notifications import Notification
from apps.notifications.push_service import PushService

logger = logging.getLogger('django.notifications')


@shared_task(bind=True)
def send_push_notifications(
    self,
    game_id,
    notification_type
):
    """
    Send notifications about a specific game.
    
    Args:
        game_id: Game ID
        notification_type: Type of notification (IN_GAME, RATE, REMOVED)

    """
    try:
        push_service = PushService()
        logger.info(
            f'Executing task: send_game_notification for game {game_id}, '
            f'type: {notification_type}'
        )
        
        result = push_service.process_notifications_by_type(
            type=notification_type,
            game_id=game_id,
        )
        
        if result:
            logger.info(f'Successfully sent notifications for game {game_id}')
        else:
            logger.warning(f'No notifications sent for game {game_id}')
            
        return (
            f'Notification task for game {game_id} '
            f'completed with result: {result}'
        )
    except Exception as e:
        logger.error(
            f'Error sending notification for game {game_id}: {str(e)}',
            exc_info=True
        )
        self.retry(exc=e, countdown=RETRY_PUSH_TIME, max_retries=MAX_RETRIES)


@shared_task(bind=True)
def retry_notification_task(
    self,
    token,
    notification_type,
    game_id=None
    ):
    """
    Retry sending notification to a specific token.
    
    Args:
        token: Device token to retry
        notification_type: Type of notification 
        game_id: Game ID if applicable
    """
    try:
        logger.info(f'Retrying notification to token {token[:8]}...')
        notification = Notification(notification_type)
        push_service = PushService()
        result = push_service.send_notification_by_token(
            token=token,
            notification=notification,
            game_id=game_id
        )
        if result:
            logger.info(f'Retry successful for token {token[:8]}...')
        else:
            logger.warning(f'Retry failed for token {token[:8]}...')   
        return result
    except Exception as e:
        logger.error(f'Error in retry task: {str(e)}', exc_info=True)
        self.retry(
            exc=e,
            countdown=RETRY_PUSH_TIME,
            max_retries=MAX_RETRIES - 1
        )
