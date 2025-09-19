from django.db import models


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

DEVICE_TOKEN_MAX_LENGTH: int = 255
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

