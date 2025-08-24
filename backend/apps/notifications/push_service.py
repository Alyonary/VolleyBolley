import logging
from threading import Lock

from pyfcm import FCMNotification
from pyfcm.errors import FCMError

from apps.notifications.constants import Notification, NotificationTypes
from apps.notifications.models import Device
from volleybolley.settings import FCM_FILE_PATH

logger = logging.getLogger('django.notifications')


class PushService:
    """
    Singleton PushService class to handle FCM push notifications.
    """
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        try:
            self._check_fcm_file()
            self.push_service = FCMNotification(
                service_account_file=FCM_FILE_PATH
            )
            self.enable = True
            logger.info('FCM service connected successfully')
        except FCMError as e:
            self.enable = False
            error_msg = f'FCM service initialization failed: {str(e)}'
            logger.error(error_msg, exc_info=True)
        except FileNotFoundError as e:
            self.enable = False
            error_msg = f'FCM service account file not found: {str(e)}'
            logger.error(error_msg, exc_info=True)
        except Exception as e:
            self.enable = False
            error_msg = f'Unexpected error initializing FCM service: {str(e)}'
            logger.error(error_msg, exc_info=True)
        finally:
            self._initialized = True

    def _check_fcm_file(self):
        """
        Check if the FCM service account file exists.
        """
        if not FCM_FILE_PATH.exists():
            error_msg = (
                f'FCM service account file not found: {FCM_FILE_PATH}'
            )
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        logger.debug(f'FCM file exists at {FCM_FILE_PATH}')
        return True

    def proccess_notifications_by_type(
        self,
        type: str,
        player_id: int | None = None,
        game_id: int | None = None,
    ) -> bool | None:
        """
        Send notifications to multiple devices using FCM.

        Args:
            type (str): Type of notification to send.
            player_id (int, optional): Player ID for player-specific 
                notifications.
            game_id (int, optional): Game ID to include in the 
                notification data.
        """
        try:
            if not self.enable:
                logger.error(
                    'Push service is not available, '
                    'cannot send notifications'
                )
                return None
            logger.info(f'Processing notification type: {type}')
            notification = Notification(type)
            
            if type == NotificationTypes.IN_GAME:
                tokens = Device.objects.active().in_game(
                    game_id
                ).values_list('token', flat=True)
                if not tokens:
                    logger.info(
                        f'No active devices found for game_id={game_id}'
                    )
                    return None
                return self.send_push_notification(
                    tokens,
                    notification,
                    game_id=game_id
                )
            elif type == NotificationTypes.RATE:
                tokens = Device.objects.active().in_game(
                    game_id
                ).values_list('token', flat=True)
                if not tokens:
                    logger.info(
                        f'No active devices found for game_id={game_id}'
                    )
                    return None
                return self.send_push_notification(
                    tokens,
                    notification,
                    game_id=game_id
                )
            elif type == NotificationTypes.REMOVED:
                tokens = Device.objects.active().by_player(
                    player_id
                ).values_list('token', flat=True)
                if not tokens:
                    logger.info(
                        f'No active devices found for player_id={player_id}'
                    )
                    return None
                return self.send_push_notification(
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

    def send_push_notifications(
        self,
        tokens: list[str],
        notification: Notification,
        game_id: int | None = None,
    ) -> bool | None:
        """
        Send push notifications to multiple devices.

        Args:
            tokens (list): List of device tokens to send the notification to.
            notification (Notification): Notification object containing title,
                body, and screen.
            game_id (int, optional): Game ID to include in the 
                notification data.
        """
        for token in tokens:
            self.send_notification_by_token(
                token=token,
                notification=notification,
                game_id=game_id
            )
        return True

    def send_notification_by_token(
        self,
        token: str,
        notification: Notification,
        game_id: int | None = None,
    ) -> bool | None:
        """
        Send push notification to a single device.

        Args:
            token (str): Device token to send the notification to.
            notification (Notification): Notification object containing title,
                body, and screen.
            game_id (int, optional): Game ID to include in the 
                notification data.
        """
        if not self.enable:
            logger.error(
                'Push service is not available, cannot send notifications'
            )
            return False
        data_message = {'screen': notification.screen}
        if game_id:
            data_message['gameId'] = game_id
        error_occurred = False
        try:
            masked_token = token[:8] + '...' if len(token) > 8 else token
            logger.debug(f'Sending notification to device {masked_token}')
            self.push_service.notify(
                fcm_token=token,
                notification_title=notification.title,
                notification_body=notification.body,
                data_payload=data_message
            )
            logger.debug(
                f'Notification sent successfully to device {masked_token}'
            )
            return True
        except FCMError as e:
            error_occurred = True
            logger.warning(f'FCM Error for token {masked_token}: {str(e)}')
            return False
        except Exception as e:
            error_occurred = True
            logger.error(
                f'Unexpected error sending to {masked_token}: {str(e)}'
            )
            return False
        finally:
            if error_occurred:
                # Импорт внутри функции для избежания циклического импорта
                from apps.notifications.tasks import retry_notification_task
                retry_notification_task.apply_async(
                    args=[token, notification.type, game_id],
                    countdown=60
                )
                logger.info(
                    f'Scheduled retry task for token {masked_token} '
                    f'in 60 seconds'
                )


# Функция для получения экземпляра
def get_push_service():
    """Get PushService instance."""
    return PushService()

