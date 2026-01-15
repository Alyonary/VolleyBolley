from datetime import timedelta

import pytest

from apps.notifications.constants import (
    DEV_NOTIFICATION_TIME,
    PROD_NOTIFICATION_TIME,
)
from apps.notifications.models import NotificationsTime


@pytest.mark.django_db
class TestNotificationsTime:
    """Tests for the NotificationsTime model."""

    def test_signals_create_notification_time_settings(self):
        """Test that signals create two default NotificationsTime instances."""
        notifications = NotificationsTime.objects.all()
        assert notifications.count() == 2

        develop_settings = NotificationsTime.objects.get(
            name=DEV_NOTIFICATION_TIME.name
        )
        production_settings = NotificationsTime.objects.get(
            name=PROD_NOTIFICATION_TIME.name
        )
        assert develop_settings.is_active is DEV_NOTIFICATION_TIME.is_active
        assert (
            production_settings.is_active is PROD_NOTIFICATION_TIME.is_active
        )

    def test_create_notifications_time(self):
        """Test creating a NotificationsTime instance."""
        notification = NotificationsTime.objects.create(
            name='Test Notifications Time',
            closed_event_notification=timedelta(hours=2),
            pre_event_notification=timedelta(minutes=30),
            advance_notification=timedelta(days=1),
            is_active=True,
        )

        assert notification.name == 'Test Notifications Time'
        assert notification.closed_event_notification == timedelta(hours=2)
        assert notification.pre_event_notification == timedelta(minutes=30)
        assert notification.advance_notification == timedelta(days=1)
        assert notification.is_active is True

    def test_get_active(self):
        """Test the get_active class method."""
        NotificationsTime.objects.create(
            name='Inactive Notifications Time',
            is_active=False,
        )
        active_notification = NotificationsTime.objects.create(
            name='Active Notifications Time',
            is_active=True,
        )

        result = NotificationsTime.get_active()
        assert result == active_notification
        assert result.is_active is True

    def test_get_pre_event_time(self):
        """Test the get_pre_event_time class method."""
        NotificationsTime.objects.create(
            name='Test Notifications Time',
            pre_event_notification=timedelta(minutes=45),
            is_active=True,
        )

        result = NotificationsTime.get_pre_event_time()
        assert result == timedelta(minutes=45)
        assert isinstance(result, timedelta)

    def test_get_closed_event_notification_time(self):
        """Test the get_closed_event_notification_time class method."""
        NotificationsTime.objects.create(
            name='Test Notifications Time',
            closed_event_notification=timedelta(hours=3),
            is_active=True,
        )

        result = NotificationsTime.get_closed_event_notification_time()
        assert isinstance(result, timedelta)
        assert result == timedelta(hours=3)

    def test_get_advance_notification_time(self):
        """Test the get_advance_notification_time class method."""
        NotificationsTime.objects.create(
            name='Test Notifications Time',
            advance_notification=timedelta(days=2),
            is_active=True,
        )
        result = NotificationsTime.get_advance_notification_time()
        assert isinstance(result, timedelta)
        assert result == timedelta(days=2)

    def test_only_one_active_instance(self):
        """Test that only one NotificationsTime instance can be active."""
        NotificationsTime.objects.create(
            name='First Active Notifications Time',
            is_active=True,
        )
        second_active = NotificationsTime.objects.create(
            name='Second Active Notifications Time',
            is_active=True,
        )

        first_active = NotificationsTime.objects.get(
            name='First Active Notifications Time'
        )
        assert first_active.is_active is False
        assert second_active.is_active is True
