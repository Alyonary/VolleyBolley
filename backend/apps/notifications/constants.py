from datetime import timedelta

from django.conf import settings
from django.db import models


class CeleryInspectorMessages:
    TASK_CREATED: str = 'Task successfully created.'
    WORKERS_NOT_READY: str = 'Celery workers not ready.'


CELERY_INSPECTOR_TIMEOUT: float = 2.0


class DeviceType(models.TextChoices):
    """Device type choices for push notifications."""

    IOS = 'ios', 'ios'
    ANDROID = 'android', 'android'


class NotificationTypes:
    """Notification types constants."""

    GAME_INVITE: str = 'game_join'
    GAME_REMINDER: str = 'game_reminder'
    GAME_RATE: str = 'game_rate'
    GAME_REMOVED: str = 'game_removed'

    TOURNEY_INVITE: str = 'tourney_join'
    TOURNEY_REMINDER: str = 'tourney_reminder'
    TOURNEY_RATE: str = 'tourney_rate'
    TOURNEY_REMOVED: str = 'tourney_removed'
    CHOICES = [
        (GAME_INVITE, 'game_join'),
        (GAME_REMINDER, 'game_reminder'),
        (GAME_RATE, 'game_rate'),
        (GAME_REMOVED, 'game_removed'),
        (TOURNEY_INVITE, 'tourney_join'),
        (TOURNEY_REMINDER, 'tourney_reminder'),
        (TOURNEY_RATE, 'tourney_rate'),
        (TOURNEY_REMOVED, 'tourney_removed'),
    ]
    FOR_GAMES: tuple[str] = GAME_INVITE, GAME_RATE, GAME_REMINDER, GAME_REMOVED
    FOR_TOURNEYS: tuple[str] = (
        TOURNEY_INVITE,
        TOURNEY_RATE,
        TOURNEY_REMINDER,
        TOURNEY_REMOVED,
    )


FCM_TOKEN_EXPIRY_DAYS: int = 270
DEVICE_TOKEN_MAX_LENGTH: int = 255
DEVICE_PLATFORM_LENGTH: int = 32
MAX_RETRIES: int = 3
NOTIFICATION_TYPE_MAX_LENGTH: int = 32
NOTIFICATION_TITLE_MAX_LENGTH: int = 128
NOTIFICATION_SCREEN_MAX_LENGTH: int = 64
NOTIFICATION_INIT_DATA = {
    NotificationTypes.GAME_INVITE: {
        'title': 'Game Invitation',
        'body': 'You are invited to a game!',
        'screen': 'inGame',
    },
    NotificationTypes.GAME_REMINDER: {
        'title': 'Your game is starting soon',
        'body': 'Your game is starting soon!',
        'screen': 'inGame',
    },
    NotificationTypes.GAME_RATE: {
        'title': 'Rate the players',
        'body': 'Rate players after the game.',
        'screen': 'rate',
    },
    NotificationTypes.GAME_REMOVED: {
        'title': 'You have been removed from the game',
        'body': 'See details in the app.',
        'screen': 'removed',
    },
    NotificationTypes.TOURNEY_INVITE: {
        'title': 'Tournament Invitation',
        'body': 'You are invited to a tournament!',
        'screen': 'inTourney',
    },
    NotificationTypes.TOURNEY_REMINDER: {
        'title': 'Your tournament is starting soon',
        'body': 'Your tournament is starting soon!',
        'screen': 'inTourney',
    },
    NotificationTypes.TOURNEY_REMOVED: {
        'title': 'You have been removed from the tournament',
        'body': 'See details in the app.',
        'screen': 'removed',
    },
    NotificationTypes.TOURNEY_RATE: {
        'title': 'Rate the tournament players',
        'body': 'Rate players after the tournament.',
        'screen': 'rate',
    },
}

RETRY_PUSH_TIME: int = 60


class NotificationTimePreset:
    """Preset for notification time settings."""

    def __init__(self, name, closed_event, pre_event, advance, is_active):
        self.name: str = name
        self.closed_event: timedelta = closed_event
        self.pre_event: timedelta = pre_event
        self.advance: timedelta = advance
        self.is_active: bool = is_active


DEV_NOTIFICATION_TIME = NotificationTimePreset(
    name='Develop Notification Time Settings',
    closed_event=timedelta(minutes=2),
    pre_event=timedelta(minutes=5),
    advance=timedelta(minutes=10),
    is_active=settings.DEBUG,
)

PROD_NOTIFICATION_TIME = NotificationTimePreset(
    name='Production Notification Time Settings',
    closed_event=timedelta(hours=1),
    pre_event=timedelta(hours=1),
    advance=timedelta(hours=24),
    is_active=not settings.DEBUG,
)


class PushServiceMessages:
    """Messages used in Push Service responses."""

    NO_DEVICES_FOUND: str = 'No devices found for player'
    NOTIFICATION_TYPE_NOT_FOUND: str = 'Notification type not found'
    NO_DEVICES_FOR_EVENT: str = 'Not found any devices to send message'
    ALL_NOT_DELIVERED: str = 'All notifications failed'
    EMPTY_TOKEN: str = 'Empty device token, skipping notification'
    SUCCESS: str = 'Notification sent successfully'
    SERVICE_UNAVAILABLE: str = 'Push service unavailable'
    ANSWER_SAMPLE: dict[str | bool | int] = {
        'success': False,
        'total_devices': 0,
        'delivered': 0,
        'failed': 0,
        'message': '',
        'notification_type': None,
        'notifications_data': None,
    }
