from django.db import models


class DeviceType(models.TextChoices):
    """Device type choices for push notifications."""

    IOS = 'ios', 'ios'
    ANDROID = 'android', 'android'

class NotificationTypes:
    """Notification types constants."""

    IN_GAME: str = 'game_join'
    IN_TOURNEY: str = 'tourney_join'
    RATE: str = 'rate'
    REMOVED_GAME: str = 'game_removed'
    REMOVED_TOURNEY: str = 'tourney_removed'
    CHOICES = (
        (IN_GAME, 'game_join'),
        (REMOVED_GAME, 'game_removed'),
        (IN_TOURNEY, 'tourney_join'),
        (REMOVED_TOURNEY, 'tourney_removed'),
        (RATE, 'rate'),
    )


DEVICE_TOKEN_MAX_LENGTH: int = 255
MAX_RETRIES: int = 3
NOTIFICATION_TYPE_MAX_LENGTH: int = 32
NOTIFICATION_TITLE_MAX_LENGTH: int = 128
NOTIFICATION_SCREEN_MAX_LENGTH: int = 64
NOTIFICATION_INIT_DATA = {
    NotificationTypes.IN_GAME: {
        'title': 'Game Invitation',
        'body': 'You are invited to a game!',
        'screen': 'inGame',
    },
    NotificationTypes.RATE: {
        'title': 'Rate the game',
        'body': 'Rate players after the game.',
        'screen': 'rate',
    },
    NotificationTypes.REMOVED_GAME: {
        'title': 'You have been removed from the game',
        'body': 'See details in the app.',
        'screen': 'removed',
    },
    NotificationTypes.IN_TOURNEY: {
        'title': 'Tournament Invitation',
        'body': 'You are invited to a tournament!',
        'screen': 'inTourney',
    },
    NotificationTypes.REMOVED_TOURNEY: {
        'title': 'You have been removed from the tournament',
        'body': 'See details in the app.',
        'screen': 'removed',
    },
}

RETRY_PUSH_TIME: int = 60
