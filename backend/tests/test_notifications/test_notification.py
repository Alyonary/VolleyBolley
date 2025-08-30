import pytest

from apps.notifications.notifications import (
    InGameNotification,
    Notification,
    NotificationTypes,
    RateNotification,
    RemovedNotification,
)


def test_in_game_notification_singleton():
    """Test InGameNotification singleton and its fields."""
    notif1 = InGameNotification()
    notif2 = InGameNotification()
    assert notif1 is notif2
    assert notif1.type == NotificationTypes.IN_GAME
    assert notif1.title == 'Game Invitation'
    assert notif1.body == 'You are invited to a game!'
    assert notif1.screen == 'inGame'


def test_rate_notification_singleton():
    """Test RateNotification singleton and its fields."""
    notif1 = RateNotification()
    notif2 = RateNotification()
    assert notif1 is notif2
    assert notif1.type == NotificationTypes.RATE
    assert notif1.title == 'Rate the game'
    assert notif1.body == 'Please rate the game!'
    assert notif1.screen == 'rate'


def test_removed_notification_singleton():
    """Test RemovedNotification singleton and its fields."""
    notif1 = RemovedNotification()
    notif2 = RemovedNotification()
    assert notif1 is notif2
    assert notif1.type == NotificationTypes.REMOVED
    assert notif1.title == 'You have been removed from the game'
    assert notif1.body == 'See details in the app.'
    assert notif1.screen == 'removed'


def test_notification_factory_in_game():
    """Test Notification factory returns InGameNotification."""
    notif = Notification(NotificationTypes.IN_GAME)
    assert isinstance(notif, InGameNotification)
    assert notif.type == NotificationTypes.IN_GAME
    assert notif.title == 'Game Invitation'
    assert notif.body == 'You are invited to a game!'
    assert notif.screen == 'inGame'


def test_notification_factory_rate():
    """Test Notification factory returns RateNotification."""
    notif = Notification(NotificationTypes.RATE)
    assert isinstance(notif, RateNotification)
    assert notif.type == NotificationTypes.RATE
    assert notif.title == 'Rate the game'
    assert notif.body == 'Please rate the game!'
    assert notif.screen == 'rate'


def test_notification_factory_removed():
    """Test Notification factory returns RemovedNotification."""
    notif = Notification(NotificationTypes.REMOVED)
    assert isinstance(notif, RemovedNotification)
    assert notif.type == NotificationTypes.REMOVED
    assert notif.title == 'You have been removed from the game'
    assert notif.body == 'See details in the app.'
    assert notif.screen == 'removed'


def test_notification_factory_unknown_type():
    """Test Notification factory raises ValueError for unknown type."""
    with pytest.raises(ValueError):
        Notification('unknownType')

def test_notification_requires_type():
    """Test Notification requires a type argument."""
    with pytest.raises(ValueError):
        Notification(None)