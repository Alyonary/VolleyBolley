import json
import logging
import os
from functools import wraps

import firebase_admin
from backend.apps.notifications.inspectors import (
    CeleryInspector,
    RedisInspector,
)
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import DatabaseError, IntegrityError
from firebase_admin import credentials
from pyfcm import FCMNotification
from pyfcm.errors import FCMError

from apps.core.base import BaseConnectionManager
from apps.event.models import Game, Tourney
from apps.notifications.constants import (
    RETRY_PUSH_TIME,
    NotificationTypes,
)
from apps.notifications.messages import (
    ConnectionLogMessages,
    PushServiceMessages,
    RepositoryLogMessages,
    SenderLogMessages,
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
    def wrapper(self: 'PushService', *args, **kwargs):
        result = PushServiceMessages.ANSWER_SAMPLE.copy()

        if not self.enable:
            logger.warning(
                ConnectionLogMessages.SERVICE_MISSING.format(
                    func=func.__name__
                )
            )
            if not self.connector.reconnect():
                logger.warning(
                    ConnectionLogMessages.RECONNECT_SUCCESS.format(
                        func.__name__
                    )
                )
                result['message'] = PushServiceMessages.SERVICE_UNAVAILABLE
                return result
        return func(self, *args, **kwargs)

    return wrapper


class PushServiceConnector(BaseConnectionManager):
    """
    Singleton class for managing connections to Firebase Cloud Messaging (FCM)
    and Celery services. Handles initialization, status checking, and
    reconnection logic for push notification infrastructure.
    """

    def __init__(
        self,
        main_service: 'PushService',
        worker: CeleryInspector,
        broker: RedisInspector,
    ):
        super().__init__(worker, broker)
        self.main_service = main_service
        self._initialize_services()

    def _initialize_services(self):
        """Initialize FCM and Celery services."""
        self.enable = False
        error_msg: str = ''
        try:
            self.fb_available = self._initialize_firebase()
            self.celery_available = self._check_celery_availability()
            if self.fb_available and self.celery_available:
                self.enable = True
                logger.info(ConnectionLogMessages.INIT_SUCCESS)
            if not self.fb_available:
                error_msg = ConnectionLogMessages.FCM_FAIL
            if not self.celery_available:
                error_msg += ConnectionLogMessages.CELERY_FAIL
        except Exception as e:
            error_msg = ConnectionLogMessages.INIT_UNEXPECTED_ERROR.format(
                error=str(e)
            )
        finally:
            if error_msg:
                self.enable = False
                logger.error(
                    ConnectionLogMessages.INIT_FAILED.format(
                        error=str(error_msg)
                    ),
                    exc_info=True,
                )

    def _get_fcm_file_path(self) -> str:
        """Return path to fcm.json in BASE_DIR."""
        return os.path.join(settings.BASE_DIR, 'fcm_service_account.json')

    def _fcm_file_exists(self) -> bool:
        """Check if fcm.json exists in BASE_DIR."""
        return os.path.isfile(self._get_fcm_file_path())

    def __bool__(self):
        """Return True if notifications services are available."""
        return all(self.get_status().values())

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
        logger.info(
            ConnectionLogMessages.FCM_FILE_CREATED.format(path=file_path)
        )

    def _initialize_firebase(self):
        """Initialize Firebase app if not already initialized."""
        try:
            cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT)
            if not firebase_admin._apps:
                firebase_admin.initialize_app(cred)
            self.fb_admin = firebase_admin.get_app()
            logger.info(ConnectionLogMessages.FCM_ADMIN_OK)
            fcm_file_path = self._get_fcm_file_path()
            if not self._fcm_file_exists():
                self._create_fcm_file()
            self.push_service = FCMNotification(
                service_account_file=fcm_file_path,
            )
            return True
        except Exception as e:
            self.fb_admin = None
            self.push_service = None
            logger.error(
                ConnectionLogMessages.INIT_FAILED.format(error=str(e))
            )
            return False

    def reconnect(self) -> bool:
        """Reconnect to FCM and Celery services."""
        with self._lock:
            logger.info(ConnectionLogMessages.RECONNECT_START)
            self._initialize_services()
            current_status = self.get_status()
            if all(current_status.values()) and self.enable:
                logger.info(ConnectionLogMessages.RECONNECT_SUCCESS)
                return True
            logger.warning(ConnectionLogMessages.RECONNECT_FAILED)
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
        return self.worker.check_connection()


class NotificationRepository:
    """
    Repository for notification-related database models. Provides methods to
    retrieve devices, notification templates, and create notification records.
    """

    def __init__(self, main_service: 'PushService'):
        self.main_service = main_service
        self.device_model = Device
        self.notification_type = NotificationsBase

    def get_devices_by_player(self, player_id: int) -> Device | None:
        """
        Get device for a specific player.
        Args:
            player_id (int): Player ID to get the device for.
        """
        return self.device_model.objects.by_player(player_id)

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
        logger.warning(
            RepositoryLogMessages.UNKNOWN_TYPE.format(
                notif_type=notification_type
            )
        )

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
            logger.error(
                RepositoryLogMessages.TYPE_NOT_FOUND.format(
                    notif_type=notification_type
                )
            )
            return None

    def bulk_create_notifications_record(
        self, notifications_data: list[dict]
    ) -> bool:
        """
        Create a database model for storing notification.
        Args:
            device (Device): Device object to associate with the notification.
            notification_type (str): Type of notification sent.
            event_id (int, optional): Game ID for the notification data.
        """
        for n_data in notifications_data:
            event_id = n_data.pop('event_id')
            if event_id:
                if (
                    n_data['notification_type'].type
                    in NotificationTypes.FOR_GAMES
                ):
                    game_obj = Game.objects.filter(id=event_id).first()
                    if game_obj:
                        n_data['game'] = game_obj
                else:  # notification.type in NotificationTypes.FOR_TOURNEYS
                    tourney_obj = Tourney.objects.filter(id=event_id).first()
                    if tourney_obj:
                        n_data['tourney'] = tourney_obj
            try:
                Notifications.objects.create(**n_data)
                logger.debug(
                    RepositoryLogMessages.DB_CREATED.format(
                        player=n_data.get('player')
                    )
                )
            except IntegrityError as e:
                logger.error(
                    RepositoryLogMessages.DB_CREATION_ERROR.format(
                        player=n_data.get('player'),
                        error=f'Integrity check failed: {e}',
                    )
                )
            except ValidationError as e:
                logger.error(
                    RepositoryLogMessages.DB_CREATION_ERROR.format(
                        player=n_data.get('player'),
                        error=f'Validation failed: {e}',
                    )
                )
            except DatabaseError as e:
                logger.error(
                    RepositoryLogMessages.DB_CREATION_ERROR.format(
                        player=n_data.get('player'),
                        error=f'Database error: {e}',
                    ),
                    exc_info=True,
                )
            except Exception as e:
                logger.critical(
                    RepositoryLogMessages.DB_CREATION_ERROR.format(
                        player=n_data.get('player'),
                        error=f'Unexpected error: {e}',
                    ),
                    exc_info=True,
                )
                continue
        return


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

    def send_push_bulk(
        self,
        devices: list[Device],
        notification: NotificationsBase,
        event_id: int | None = None,
    ):
        result = PushServiceMessages.ANSWER_SAMPLE.copy()
        result['notification_type'] = notification.type
        result['total_devices'] = len(devices)
        result['notifications_data'] = []

        if not notification:
            logger.error(
                RepositoryLogMessages.TYPE_NOT_FOUND.format(notif_type='None')
            )
            result['message'] = PushServiceMessages.NOTIFICATION_TYPE_NOT_FOUND
            return result

        if not devices:
            logger.info(PushServiceMessages.NO_DEVICES_FOR_EVENT)
            result['message'] = PushServiceMessages.NO_DEVICES_FOR_EVENT
            return result

        for d in devices:
            status, message = self._send_notification_by_device_internal(
                device=d,
                notification=notification,
                event_id=event_id,
            )
            if status:
                result['notifications_data'].append(
                    {
                        'player': d.player,
                        'notification_type': notification,
                        'event_id': event_id,
                    }
                )
                result['delivered'] += 1
                continue
            result['failed'] += 1

        logger.info(
            SenderLogMessages.PUSH_RESULTS.format(
                notif_type=notification.type,
                delivered=result['delivered'],
                total=result['total_devices'],
                failed=result['failed'],
            )
        )

        if result['delivered'] > 0:
            result['success'] = True
            result['message'] = PushServiceMessages.SUCCESS
        else:
            result['message'] = PushServiceMessages.ALL_NOT_DELIVERED
        return result

    def _send_notification_by_device_internal(
        self,
        device: Device,
        notification: NotificationsBase,
        event_id: int | None = None,
    ) -> tuple[bool, str]:
        """
        Internal method to send push notification to a single device.
        """
        error_occurred = False
        if not device.token:
            m = PushServiceMessages.EMPTY_TOKEN
            logger.warning(SenderLogMessages.EMPTY_TOKEN)
            return False, m

        data_message = {'screen': notification.screen}
        if event_id:
            data_message['gameId'] = str(event_id)

        masked_token = f'{device.token[:8]}...'

        try:
            logger.debug(
                SenderLogMessages.SENDING_TO.format(token=masked_token)
            )
            self.push_service.notify(
                fcm_token=device.token,
                notification_title=notification.title,
                notification_body=notification.body,
                data_payload=data_message,
            )
            logger.debug(
                SenderLogMessages.SEND_SUCCESS.format(token=masked_token)
            )
            return True, 'success'

        except FCMError as e:
            error_occurred = True
            m = SenderLogMessages.FCM_SEND_ERROR.format(
                token=masked_token, error=str(e)
            )
            logger.warning(m, exc_info=True)
            return False, m
        except Exception as e:
            error_occurred = True
            m = SenderLogMessages.UNEXPECTED_SEND_ERROR.format(
                token=masked_token, error=str(e)
            )
            logger.error(m, exc_info=True)
            return False, m
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
                        SenderLogMessages.RETRY_SCHEDULED.format(
                            token=masked_token, time=RETRY_PUSH_TIME
                        )
                    )
                except Exception as celery_error:
                    logger.error(
                        SenderLogMessages.RETRY_FAILED.format(
                            token=masked_token, error=str(celery_error)
                        )
                    )


class PushService:
    """
    Facade for push notification system. Manages repository, connector, and
    sender components. Exposes high-level methods for sending notifications
    to devices or groups.
    """

    def __init__(self):
        self.repository = NotificationRepository(main_service=self)
        self.connector = PushServiceConnector(
            main_service=self,
            worker=CeleryInspector(),
            broker=RedisInspector(),
        )
        self.sender = PushNotificationSender(main_service=self)

    def __bool__(self):
        """Return True if push service is enabled."""
        return bool(self.connector)

    @service_required
    def send_to_player(
        self,
        player_id: int,
        notification_type: str,
        event_id: int | None = None,
    ) -> dict | bool:
        result = self.sender.send_push_bulk(
            devices=self.repository.get_devices_by_player(player_id),
            notification=self.repository.get_notification_object(
                notification_type=notification_type
            ),
            event_id=event_id,
        )
        notifications_data = result.pop('notifications_data')
        if notifications_data:
            self.repository.bulk_create_notifications_record(
                notifications_data
            )
        return result

    @service_required
    def send_push_for_event(
        self,
        notification_type: str,
        event_id: int | None = None,
    ) -> dict[str, int]:
        result = self.sender.send_push_bulk(
            devices=self.repository.get_devices(
                notification_type=notification_type,
                event_id=event_id,
            ),
            notification=self.repository.get_notification_object(
                notification_type=notification_type
            ),
            event_id=event_id,
        )
        notifications_data = result.pop('notifications_data')
        if notifications_data:
            self.repository.bulk_create_notifications_record(
                notifications_data
            )
        return result

    def reconnect(self) -> bool:
        """Reconnect to push notification services."""
        return self.connector.reconnect()

    @property
    def enable(self) -> bool:
        """Return True if push service is enabled."""
        return self.connector.enable
