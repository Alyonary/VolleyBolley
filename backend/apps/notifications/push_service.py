import json
import logging
import os
from functools import wraps
from threading import Lock

import firebase_admin
from celery import current_app
from django.conf import settings
from firebase_admin import credentials
from pyfcm import FCMNotification
from pyfcm.errors import FCMError

from apps.notifications.models import Device, Notifications
from apps.notifications.notifications import (
    Notification,
    NotificationsClass,
    NotificationTypes,
)

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
                f'attempting reconnection'
            )
            if not self.reconnect():
                logger.warning(
                    f'Service unavailable, skipping {func.__name__}'
                )
                return None
        if not self.enable:
            logger.error(
                f'Service still unavailable after reconnection attempt '
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
    Arguments:
        enable (bool): Flag to enable/disable push notifications.
    Attributes:
        fb_admin: Firebase app instance.
        push_service: FCMNotification instance for sending notifications.
        fb_available (bool): Flag  if FCM service is available.
        celery_available (bool): Flag if Celery workers are available.
        _initialized (bool): Flag if services have been initialized.
    Methods:
        reconnect(): Attempts to reconnect to FCM and Celery services.
        get_status(): Returns current status of services.
        process_notifications_by_type(type, player_id=None, game_id=None):
            Sends notifications to multiple devices using FCM.
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
        error_msg: str = ''
        try:
            self.fb_available = self._initialize_firebase()
            self.celery_available = self._check_celery_availability()
            if self.fb_available and self.celery_available:
                self.enable = True
                logger.info(
                    'Firebase and Celery services connected successfully, '
                    'notifications enabled'
                )
            if not self.fb_available:
                error_msg = 'FCM service not available\n'
            if not self.celery_available:
                error_msg += ' Celery workers not available'
        except Exception as e:
            error_msg = f'Unexpected error during initialization: {str(e)}'
        finally:
            if error_msg:
                self.enable = False
                logger.error(
                    f'Error initializing services: {error_msg}', exc_info=True
                )
            self._initialized = True

    def _get_fcm_file_path(self) -> str:
        """Return path to fcm.json in BASE_DIR."""
        return os.path.join(settings.BASE_DIR, 'fcm_service_account.json')

    def _fcm_file_exists(self) -> bool:
        """Check if fcm.json exists in BASE_DIR."""
        return os.path.isfile(self._get_fcm_file_path())

    def _create_fcm_file(self):
        """Create fcm.json from FIREBASE_SERVICE_ACCOUNT in BASE_DIR."""
        file_path = self._get_fcm_file_path()
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(
                settings.FIREBASE_SERVICE_ACCOUNT,
                f,
                indent=2,
                ensure_ascii=False,
            )
        logger.info(f'FCM file created at {file_path}')

    def _initialize_firebase(self):
        """Initialize Firebase app if not already initialized."""
        try:
            cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT)
            if not firebase_admin._apps:
                firebase_admin.initialize_app(cred)
            self.fb_admin = firebase_admin.get_app()
            logger.info('FB_admin initialized successfully')
            fcm_file_path = self._get_fcm_file_path()
            if not self._fcm_file_exists():
                self._create_fcm_file()
            self.push_service = FCMNotification(
                service_account_file=fcm_file_path,
            )
            logger.info('Firebase app initialized successfully')
            return True
        except Exception as e:
            self.fb_admin = None
            self.push_service = None
            logger.error(f'Error initializing Firebase app: {str(e)}')
            return False

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
            'fcm_available': self._check_fcm(),
            'celery_available': getattr(self, 'celery_available', False),
            'initialized': getattr(self, '_initialized', False),
        }

    def _check_fcm(self) -> bool:
        """Check if FCM service is available."""
        return all(
            [
                getattr(self, 'fb_admin', False),
                getattr(self, 'push_service', False),
            ]
        )

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
        Logs and returns statistics of successful and failed notifications.
        Args:
            type (str): Type of notification to send.
            player_id (int, optional): Player ID for player-specific
                notifications.
            game_id (int, optional):
                Game ID to include in the notification data.
        Returns:
            dict: Statistics of notification sending.
        """
        try:
            logger.info(f'Processing notification type: {type}')
            notification = Notification(type)
            if (
                type == NotificationTypes.IN_GAME
                or type == NotificationTypes.RATE
            ):
                devices: list[Device] = Device.objects.in_game(game_id)
            elif type == NotificationTypes.REMOVED:
                devices: list[Device] = Device.objects.by_player(player_id)
            else:
                devices = []
                logger.warning(f'Unknown notification type: {type}')
            return self.send_push_notifications(
                devices=devices, notification=notification, game_id=game_id
            )

        except Exception as e:
            err_msg = f'Error processing notification type {type}: {str(e)}'
            logger.error(err_msg, exc_info=True)
            return {'status': f'Error: Notification creation failed: {str(e)}'}

    @service_required
    def send_push_notifications(
        self,
        devices: list[Device],
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
            'total_devices': len(devices),
            'successful': 0,
            'failed': 0,
        }
        if not devices:
            logger.warning('No devices provided, skipping notification')
            return result
        for d in devices:
            is_notify = self._send_notification_by_device_internal(
                device=d, notification=notification, game_id=game_id
            )
            if is_notify:
                result['successful'] += 1
                continue
            result['failed'] += 1
        logger.info(
            f"Push notification '{notification.type}' results: "
            f"{result['successful']}/{result['total_devices']} successful, "
            f"{result['failed']} failed"
        )
        return result

    @service_required
    def send_notification_by_device(
        self,
        device: Device,
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
        if not device.token:
            logger.warning('Empty token provided, skipping notification')
            return False
        return self._send_notification_by_device_internal(
            device, notification, game_id
        )

    def _send_notification_by_device_internal(
        self,
        device: Device,
        notification: NotificationsClass,
        game_id: int | None = None,
    ) -> bool | None:
        """
        Internal method to send push notification to a single device.
        This method is NOT decorated with @service_required
        to avoid double checking.
        """
        error_occurred = False
        if not device.token:
            logger.warning('Empty device token, skipping notification')
            return False
        data_message = {'screen': notification.screen}
        if game_id:
            data_message['gameId'] = str(game_id)

        masked_token = device.token[:8] + '...'
        try:
            logger.debug(f'Sending notification to device {masked_token}')
            self.push_service.notify(
                fcm_token=device.token,
                notification_title=notification.title,
                notification_body=notification.body,
                data_payload=data_message,
            )
            logger.debug(
                f'Notification sent successfully to device {masked_token}'
            )
            self.create_db_model(device, notification.type, game_id)
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
                        args=[device.token, notification.type, game_id],
                        countdown=60,
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

    def create_db_model(
        self,
        device: Device,
        notification_type: str,
        game_id: int | None = None,
    ) -> bool:
        """
        Create a database model for storing notification.
        Args:
            device (Device): Device object to associate with the notification.
            notification_type (str): Type of notification sent.
            game_id (int, optional): Game ID for the notification data.
        """
        data = {'player': device.player, 'type': notification_type}
        if game_id:
            data['game_id'] = game_id
        try:
            Notifications.objects.create(**data)
            logger.debug(
                f'Notification DB model created for player '
                f'{device.player.user.username}'
            )
        except Exception as e:
            logger.error(
                f'Error creating notification DB model for player '
                f'{device.player.user.username}: {str(e)}',
                exc_info=True,
            )
            return False
        return True