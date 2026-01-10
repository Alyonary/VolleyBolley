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

from apps.event.models import Game, Tourney
from apps.notifications.constants import (
    RETRY_PUSH_TIME,
    NotificationTypes,
)
from apps.notifications.models import (
    Device,
    Notifications,
    NotificationsBase,
)

logger = logging.getLogger(__name__)


def service_required(func):
    """
    Decorator checks if push service is available before executing method.
    If service is not available, attempts reconnection once.
    Returns None if service remains unavailable.
    """

    @wraps(func)
    def wrapper(self: 'PushNotificationSender', *args, **kwargs):
        if not self.main_service.enable:
            logger.info(
                f'Service not available for {func.__name__}, '
                f'attempting reconnection'
            )
            if not self.main_service.reconnect():
                logger.warning(
                    f'Service unavailable, skipping {func.__name__}'
                )
                return None
        if not self.main_service.enable:
            logger.error(
                f'Service still unavailable after reconnection attempt '
                f'for {func.__name__}'
            )
            return None
        return func(self, *args, **kwargs)

    return wrapper


class PushServiceConnector:
    """
    Singleton class for managing connections to Firebase Cloud Messaging (FCM)
    and Celery services. Handles initialization, status checking, and
    reconnection logic for push notification infrastructure.
    """

    _instance = None
    _lock = Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, main_service: 'PushService'):
        if self._initialized:
            return
        self.main_service = main_service
        self._initialize_services()

    def __bool__(self):
        """Return True if notifications services are available."""
        return all(self.get_status().values())

    def _initialize_services(self):
        """Initialize FCM and Celery services."""
        self.enable = False
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


class NotificationRepository:
    """
    Repository for notification-related database models. Provides methods to
    retrieve devices, notification templates, and create notification records.
    """

    def __init__(self, main_service: 'PushService'):
        self.main_service = main_service
        self.device_model = Device
        self.notification_type = NotificationsBase

    def get_device_by_player(self, player_id: int) -> Device | None:
        """
        Get device for a specific player.
        Args:
            player_id (int): Player ID to get the device for.
        """
        return self.device_model.objects.by_player(player_id).first()

    def get_devices(
        self,
        notification_type: str,
        event_id: int | None,
    ) -> list[Device]:
        """
        Get queryset of devices to send notifications to based on type.
        Args:
            type (str): Type of notification to send.
            player_id (int, optional): Player ID for player-specific
                notifications.
        Returns:
            QuerySet: QuerySet of Device objects to send notifications to.
        """
        if (
            notification_type == NotificationTypes.GAME_REMINDER
            or notification_type == NotificationTypes.GAME_RATE
        ):
            devices = self.device_model.objects.in_game(event_id)
        elif notification_type in [
            NotificationTypes.TOURNEY_REMINDER,
            NotificationTypes.TOURNEY_RATE,
        ]:
            devices = self.device_model.objects.in_tourney(event_id)
        else:
            devices = []
            logger.warning(f'Unknown notification type: {notification_type}')
        return devices

    def get_notification_object(
        self,
        notification_type: str,
    ) -> NotificationsBase | None:
        """
        Get NotificationsBase object for the given notification type.
        Args:
            type (str): Type of notification to send.
        Returns:
            Notification: NotificationsBase object with title, body, screen.
        """
        try:
            return self.notification_type.objects.get(type=notification_type)
        except self.notification_type.DoesNotExist:
            logger.error(f'Notification type {notification_type} not found')
            return None

    def create_notification_record(
        self,
        device: Device,
        notification: NotificationsBase,
        event_id: int | None = None,
    ) -> bool:
        """
        Create a database model for storing notification.
        Args:
            device (Device): Device object to associate with the notification.
            notification_type (str): Type of notification sent.
            event_id (int, optional): Game ID for the notification data.
        """
        data = {
            'player': device.player,
            'notification_type': notification,
        }
        if event_id:
            if 'game' in notification.type:
                game_obj = Game.objects.filter(id=event_id).first()
                if game_obj:
                    data['game'] = game_obj
            elif 'tourney' in notification.type:
                tourney_obj = Tourney.objects.filter(id=event_id).first()
                if tourney_obj:
                    data['tourney'] = tourney_obj
        try:
            print('Creating notification record with data:', data)
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


class PushNotificationSender:
    """
    Service for sending push notifications to devices using FCM. Provides
    methods for sending notifications to single devices or in bulk, and
    handles error processing and retry logic.
    """

    def __init__(self, main_service: 'PushService'):
        self.push_service: FCMNotification = (
            main_service.connector.push_service
        )
        self.main_service = main_service

    @service_required
    def send_push_bulk(
        self,
        devices: list[Device],
        notification_type: str,
        event_id: int | None = None,
    ):
        result = {
            'total_devices': len(devices),
            'successful': 0,
            'failed': 0,
            'message': 'success',
        }
        notification: NotificationsBase = (
            self.main_service.repository.get_notification_object(
                notification_type=notification_type
            )
        )
        if not notification:
            logger.error(f'Notification type {notification_type} not found')
            result['message'] = 'Notification type not found'
            return result
        for d in devices:
            status = self._send_notification_by_device_internal(
                device=d,
                notification=notification,
                event_id=event_id,
            )
            if status:
                self.main_service.repository.create_notification_record(
                    device=d,
                    notification=notification,
                    event_id=event_id,
                )
                result['successful'] += 1
                continue
            result['failed'] += 1
        logger.info(
            f'Push notification "{notification_type}" results: '
            f'{result["successful"]}/{result["total_devices"]} successful, '
            f'{result["failed"]} failed'
        )
        if result['successful'] == 0:
            result['message'] = 'All notifications failed'
        return result

    @service_required
    def send_notification_by_device(
        self,
        device: Device,
        notification: NotificationsBase,
        event_id: int | None = None,
    ) -> bool | None:
        """
        Public method to send push notification to a single device.
        Args:
            device (Device): Device object to send the notification to.
            notification (NotificationsBase): Notification object containing
                title, body, and screen.
            event_id (int, optional): Game ID to include in the notification
                data.
        """
        status = {'success': False}
        if not device.token:
            logger.warning('Empty token provided, skipping notification')
            return status
        if self._send_notification_by_device_internal(
            device, notification, event_id
        ):
            self.main_service.repository.create_notification_record(
                device=device,
                notification=notification,
                event_id=event_id,
            )
            status = {'success': True}
        return status

    def _send_notification_by_device_internal(
        self,
        device: Device,
        notification: NotificationsBase,
        event_id: int | None = None,
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
        if event_id:
            data_message['gameId'] = str(event_id)
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
                        args=[device.player.id, notification.type, event_id],
                        countdown=RETRY_PUSH_TIME,
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


class PushService:
    """
    Facade for push notification system. Manages repository, connector, and
    sender components. Exposes high-level methods for sending notifications
    to devices or groups.
    """

    def __init__(self):
        self.repository = NotificationRepository(main_service=self)
        self.connector = PushServiceConnector(main_service=self)
        self.sender = PushNotificationSender(main_service=self)

    def send_to_device(
        self,
        player_id: int,
        notification_type: str,
        event_id: int | None = None,
    ) -> dict | bool:
        result = {'success': False}
        device = self.repository.get_device_by_player(player_id)
        if not device:
            logger.error(f'No device found for player ID {player_id}')
            return result
        notification = self.repository.get_notification_object(
            notification_type=notification_type
        )
        if not notification:
            logger.error(f'Notification type {notification_type} not found')
            return result
        return self.sender.send_notification_by_device(
            device=device, notification=notification, event_id=event_id
        )

    def send_push_for_event(
        self,
        notification_type: str,
        event_id: int | None = None,
    ) -> dict[str, int]:
        notification = self.repository.get_notification_object(
            notification_type=notification_type
        )
        if not notification:
            logger.error(f'Notification type {notification_type} not found')
            return {
                'total_devices': 0,
                'successful': 0,
                'failed': 0,
            }
        devices = self.repository.get_devices(
            notification_type=notification_type,
            event_id=event_id,
        )
        return self.sender.send_push_bulk(
            devices=devices, notification=notification, event_id=event_id
        )

    def reconnect(self) -> bool:
        """Reconnect to push notification services."""
        return self.connector.reconnect()

    @property
    def enable(self) -> bool:
        """Return True if push service is enabled."""
        return self.connector.enable
