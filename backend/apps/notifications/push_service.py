import logging
from functools import wraps
from threading import Lock

from celery import current_app
from pyfcm import FCMNotification
from pyfcm.errors import FCMError

from apps.notifications.models import Device
from apps.notifications.notifications import (
    Notification,
    NotificationsClass,
    NotificationTypes,
)
from volleybolley.settings import FCM_FILE_PATH

logger = logging.getLogger(__name__)


def service_required(func):
    """
    Decorator checks if push service is available before executing method.
    If service is not available, attempts reconnection once.
    Returns None if service remains unavailable.
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self.enable:
            logger.info(
                f'Service not available for {func.__name__}, '
                f'attempting reconnection')
            if not self.reconnect():
                logger.warning(
                    f'Service unavailable, skipping {func.__name__}'
                )
                return None
        if not self.enable:
            logger.error(
                f'Service still unavailable after reconnection attempt'
                f'for {func.__name__}'
            )
            return None
        return func(self, *args, **kwargs)
    return wrapper


class PushService:
    """
    Singleton PushService class to handle FCM push notifications.
    Manages connection to FCM and Celery services.
    Uses double-checked locking to ensure thread-safe singleton instantiation.
    Provides methods to send notifications and check service status.
    
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
        self._initialize_services()

    def __bool__(self):
        """Return True if notifications services are available."""
        return all(self.get_status().values())

    def _initialize_services(self):
        """Initialize FCM and Celery services."""
        self.enable = False
        self.celery_available = False
        error_msg: str | None = None
        try:
            fcm_available = self._check_fcm_file()
            celery_workers_available = self._check_celery_availability()
            if fcm_available and celery_workers_available:
                self.push_service = FCMNotification(
                    service_account_file=FCM_FILE_PATH
                )
                self.enable = True
                self.celery_available = True
                logger.info('FCM and Celery services connected successfully')
            elif fcm_available and not celery_workers_available:
                self.enable = False
                self.celery_available = False
                logger.warning(
                    'FCM file exists but Celery workers not available. '
                    'Notifications disabled.'
                )
            elif not fcm_available and celery_workers_available:
                self.enable = False
                self.celery_available = True
                logger.warning(
                    'Celery workers available but FCM file not found. '
                    'Notifications disabled.'
                )
            else:
                self.enable = False
                self.celery_available = False
                logger.error(
                    'FCM and Celery workers are not available. '
                    'Notifications disabled.'
                )
        except FCMError as e:
            error_msg = f'FCM service initialization failed: {str(e)}'
        except Exception as e:
            error_msg = f'Unexpected error initializing services: {str(e)}'
        finally:
            if error_msg:
                self.enable = False
                logger.error(error_msg, exc_info=True)
            self._initialized = True

    def reconnect(self) -> bool:
        """Reconnect to FCM and Celery services."""
        with self._lock:
            logger.info('Attempting to reconnect services.')
            self._initialize_services()
            current_status = self.get_status()
            logger.info(f'Reconnection completed: {current_status}')
            if all(current_status.values()) and self.enable:
                logger.info(
                    'FCM and Celery workers are available. '
                    'Notifications enabled.'
                )
                return True
            logger.warning(
                'FCM and/or Celery workers are NOT available. '
                'Notifications disabled.'
            )
            return False

    def get_status(self) -> dict:
        """
        Get current status of services.
        
        Returns:
            dict: Current status of FCM and Celery services
        """
        return {
            'notifications_enabled': getattr(self, 'enable', False),
            'fcm_available': self._check_fcm_file(),
            'celery_available': getattr(self, 'celery_available', False),
            'initialized': getattr(self, '_initialized', False),
        }

    def _check_fcm_file(self) -> bool:
        """Check if the FCM service account file exists."""
        if not FCM_FILE_PATH.exists():
            error_msg = (
                f'FCM service account file not found: {FCM_FILE_PATH}'
            )
            logger.error(error_msg)
            return False
        logger.debug(f'FCM file exists at {FCM_FILE_PATH}')
        return True

    def _check_celery_availability(self) -> bool:
        """
        Check if Celery workers are available and working.
        
        Returns:
            bool: True if Celery workers are available, False otherwise
        """
        try:
            inspector = current_app.control.inspect(timeout=2.0)
            active_workers = inspector.active()
            if not active_workers:
                logger.warning('No active Celery workers found')
                return False
            logger.debug(f'Found {len(active_workers)} active Celery workers')
            return True
        except ImportError:
            logger.error('Celery is not installed')
            return False
        except Exception as e:
            logger.warning(f'Cannot connect to Celery: {str(e)}')
            return False

    @service_required
    def process_notifications_by_type(
        self,
        type: str,
        player_id: int | None = None,
        game_id: int | None = None,
    ) -> dict | None:
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
            logger.info(f'Processing notification type: {type}')
            notification = Notification(type)
            if type == NotificationTypes.IN_GAME:
                tokens = Device.objects.active().in_game(
                    game_id
                ).values_list('token', flat=True)
                return self.send_push_notifications(
                    tokens,
                    notification,
                    game_id=game_id
                )
            elif type == NotificationTypes.RATE:
                tokens = Device.objects.active().in_game(
                    game_id
                ).values_list('token', flat=True)
                return self.send_push_notifications(
                    tokens,
                    notification,
                    game_id=game_id
                )
            elif type == NotificationTypes.REMOVED:
                tokens = Device.objects.active().by_player(
                    player_id
                ).values_list('token', flat=True)
                return self.send_push_notifications(
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

    @service_required
    def send_push_notifications(
        self,
        tokens: list[str],
        notification: NotificationsClass,
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
        result = {
            'total_tokens': len(tokens),
            'successful': 0,
            'failed': 0,
        }
        if not tokens:
            logger.warning('No tokens provided, skipping notification')
            return result
        for token in tokens:
            is_notify = self._send_notification_by_token_internal(
                token=token,
                notification=notification,
                game_id=game_id
            )
            if is_notify:
                result['successful'] += 1
                continue
            result['failed'] += 1
        logger.info(
            f"Push notification '{notification.type}' results: "
            f"{result['successful']}/{result['total_tokens']} successful, "
            f"{result['failed']} failed"
        )
        return result

    @service_required
    def send_notification_by_token(
        self,
        token: str,
        notification: NotificationsClass,
        game_id: int | None = None,
    ) -> bool | None:
        """
        Public method to send push notification to a single device.

        Args:
            token (str): Device token to send the notification to.
            notification (Notification): Notification object containing title,
                body, and screen.
            game_id (int, optional): Game ID to include in the 
                notification data.
        """
        if not token:
            logger.warning('Empty token provided, skipping notification')
            return False
        return self._send_notification_by_token_internal(
            token,
            notification,
            game_id
        )

    def _send_notification_by_token_internal(
        self,
        token: str,
        notification: NotificationsClass,
        game_id: int | None = None,
    ) -> bool | None:
        """
        Internal method to send push notification to a single device.
        This method is NOT decorated with @service_required
        to avoid double checking.
        """
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
                try:
                    from apps.notifications.tasks import (
                        retry_notification_task,
                    )
                    retry_notification_task.apply_async(
                        args=[token, notification.type, game_id],
                        countdown=60
                    )
                    logger.info(
                        f'Scheduled retry task for token {masked_token} '
                        f'in 60 seconds'
                    )
                except Exception as celery_error:
                    logger.error(
                        f'Failed to schedule retry task for {masked_token}: '
                        f'{str(celery_error)}'
                    )
