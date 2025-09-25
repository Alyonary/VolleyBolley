from unittest.mock import Mock

import pytest

from apps.notifications.tasks import (
    retry_notification_task,
    send_push_notifications_on_upcoming_events,
)


@pytest.mark.django_db
class TestNotificationTasks:
    """Tests for notification-related Celery tasks."""

    def test_send_push_notifications_success(
        self, push_service_enabled, monkeypatch, sample_notification
    ):
        """Test send_push_notifications task success."""
        monkeypatch.setattr(
            push_service_enabled,
            'process_notifications_by_type',
            Mock(return_value={'status': True,}),
        )
        result = send_push_notifications_on_upcoming_events.run(
            event_id=1, notification_type=sample_notification.type
        )
        assert result['status'] is True
        assert push_service_enabled.process_notifications_by_type.called

    def test_send_push_notifications_none(
        self, push_service_enabled, monkeypatch, sample_notification
    ):
        """Test send_push_notifications task returns None result."""
        monkeypatch.setattr(
            push_service_enabled,
            'process_notifications_by_type',
            Mock(return_value={'status': False}),
        )
        result = send_push_notifications_on_upcoming_events.run(
            event_id=2, notification_type=sample_notification.type
        )
        assert result['status'] is False
        assert push_service_enabled.process_notifications_by_type.called

    def test_send_push_notifications_exception(
        self, monkeypatch, push_service_enabled, sample_notification
    ):
        """Test send_push_notifications retries on exception."""
        monkeypatch.setattr(
            push_service_enabled,
            'process_notifications_by_type',
            Mock(side_effect=Exception('fail')),
        )
        with pytest.raises(Exception) as exc_info:
            send_push_notifications_on_upcoming_events.run(
                event_id=3, notification_type=sample_notification.type
            )
        assert 'fail' in str(exc_info.value)

    def test_retry_notification_task_success(
        self, push_service_enabled, sample_notification, monkeypatch
    ):
        """Test retry_notification_task returns True on success."""
        monkeypatch.setattr(
            push_service_enabled,
            'send_notification_by_device',
            Mock(return_value=True),
        )
        result = retry_notification_task.run(
            token='token123',
            notification_type=sample_notification.type,
            event_id=42,
        )
        assert result is True
        assert push_service_enabled.send_notification_by_device.called

    def test_retry_notification_task_failure(
        self, push_service_enabled, sample_notification, monkeypatch
    ):
        """Test retry_notification_task returns False on failure."""
        monkeypatch.setattr(
            push_service_enabled,
            'send_notification_by_device',
            Mock(return_value=False),
        )
        result = retry_notification_task.run(
            token='token456',
            notification_type=sample_notification.type,
            event_id=99,
        )
        assert result is False
        assert push_service_enabled.send_notification_by_device.called

    def test_retry_notification_task_exception(
        self, monkeypatch, push_service_enabled, sample_notification
    ):
        """Test retry_notification_task retries on exception."""
        monkeypatch.setattr(
            push_service_enabled,
            'send_notification_by_device',
            Mock(side_effect=Exception('fail')),
        )
        with pytest.raises(Exception) as exc_info:
            retry_notification_task.run(
                token='token789',
                notification_type=sample_notification.type,
                event_id=77,
            )
        assert 'fail' in str(exc_info.value)
