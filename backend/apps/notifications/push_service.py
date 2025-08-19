import logging

from pyfcm import FCMNotification
from pyfcm.errors import FCMError

from apps.notifications.constants import Notification, NotificationTypes
from apps.notifications.exceptions import FCMFileNotFoundError, FCMServiceError
from apps.notifications.models import Device
from volleybolley.settings import FCM_FILE_PATH

# Настройка логгера
logger = logging.getLogger('django.notifications')


def initialize_push_service():
    """
    Initialize the FCM service with the service account file.
    """
    #Перенести логику проверки fcm файла в воркфлоу?? (перед запуском бэка)
    try:
        check_fcm_file()
        fcm_file_path = FCM_FILE_PATH
        push_service = FCMNotification(
            service_account_file=fcm_file_path
        )
        logger.info('FCM service connected successfully')
        return push_service
    except FCMError as e:
        error_msg = f'FCM service initialization failed: {str(e)}'
        logger.error(error_msg, exc_info=True)
        raise FCMServiceError(
                'FCM service initialization failed. '
                'Check the service account file.'
            ) from e
    except FileNotFoundError as e:
        error_msg = f'FCM service account file not found: {str(e)}'
        logger.error(error_msg, exc_info=True)
        raise FCMFileNotFoundError() from e
    except Exception as e:
        error_msg = f'Unexpected error initializing FCM service: {str(e)}'
        logger.error(error_msg, exc_info=True)
        raise FCMServiceError(f'Unexpected error: {str(e)}') from e


def check_fcm_file():
    '''
    Check if the FCM service account file exists.
    '''
    if not FCM_FILE_PATH.exists():
        error_msg = f'FCM service account file not found: {FCM_FILE_PATH}'
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    logger.debug(f'FCM file exists at {FCM_FILE_PATH}')
    return True


def proccess_notifications_by_type(
    type: str,
    player_id: int | None = None,
    game_id: int | None = None
) -> bool | None:
    '''
    Sends a notification to multiple devices using FCM.

    Args:
        tokens (list): List of device tokens to send the notification to.
        type (str): Type of notification to send.
        game_id (int, optional): Game ID to include in the notification data.
    '''
    try:
        logger.info(f'Processing notification type: {type}')
        notification = Notification(type)
        
        if type == NotificationTypes.IN_GAME:
            tokens = Device.objects.active(
                ).in_game(game_id).values_list('token', flat=True)
            if not tokens:
                logger.info(f'No active devices found for game_id={game_id}')
                return 
            return send_push_notification(
                tokens,
                notification,
                game_id=game_id
            )
        elif type == NotificationTypes.RATE:
            tokens = Device.objects.active(
                ).in_game(game_id).values_list('token', flat=True)
            if not tokens:
                logger.info(f'No active devices found for game_id={game_id}')
                return
            return send_push_notification(
                tokens,
                notification,
                game_id=game_id
            )
        elif type == NotificationTypes.REMOVED:
            tokens = Device.objects.active(
                ).by_player(player_id).values_list('token', flat=True)
            if not tokens:
                logger.info(
                    f'No active devices found for player_id={player_id}'
                )
                return
            return send_push_notification(
                tokens,
                notification,
            )
        else:
            logger.warning(f'Unknown notification type: {type}')
            return None
    except Exception as e:
        err_msg = f'Error processing notification type {type}: {str(e)}'
        logger.error(err_msg, exc_info=True)
        return None


try:
    logger.info('Initializing push service')
    push_service = initialize_push_service()
except Exception as e:
    error_msg = f'Failed to initialize push service: {str(e)}'
    logger.critical(error_msg, exc_info=True)
    push_service = None


def send_push_notification(
    tokens: list[int],
    notification: Notification,
    game_id: int | None = None,
    push_service: FCMNotification = push_service
) -> bool | None:
    '''
    Sends a push notification to multiple devices.

    Args:
        tokens (list): List of device tokens to send the notification to.
        notification (Notification): Notification object containing title,
            body, and screen.
        game_id (int, optional): Game ID to include in the notification data.
    '''
    if push_service is None:
        logger.error(
            'Push service is not initialized, cannot send notifications'
        )
        return None
    data_message = {'screen': notification.screen}
    if game_id:
        data_message['gameId'] = game_id
    for token in tokens:
        try:
            masked_token = token[:8] + '...' if len(token) > 8 else token
            logger.debug(f'Sending notification to device {masked_token}')
            push_service.notify(
                fcm_token=token,
                notification_title=notification.title,
                notification_body=notification.body,
                data_payload=data_message
            )
            logger.debug(
                f'Notification sent successfully to device {masked_token}'
            )
        except FCMError as e:
            logger.warning(f'FCM Error for token {masked_token}: {str(e)}')
            # создать задание на повторную отправку посел интеграции Celery
            continue
        except Exception as e:
            logger.error(
                f'Unexpected error sending to {masked_token}: {str(e)}'
            )
            continue
    return True