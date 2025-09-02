from unittest.mock import Mock

import pytest

from apps.notifications.tasks import (
    retry_notification_task,
    send_push_notifications,
)


def test_send_push_notifications_success(
    push_service_enabled,
    monkeypatch,
    sample_notification
):
    """Test send_push_notifications task success."""
    monkeypatch.setattr(
        push_service_enabled,
        'process_notifications_by_type',
        Mock(return_value={'successful': 2})
    )
    result = send_push_notifications.run(
        game_id=1,
        notification_type=sample_notification.type
    )
    assert 'completed with result:' in result
    assert push_service_enabled.process_notifications_by_type.called


def test_send_push_notifications_none(
    push_service_enabled,
    monkeypatch,
    sample_notification
):
    """Test send_push_notifications task returns None result."""
    monkeypatch.setattr(
        push_service_enabled,
        'process_notifications_by_type',
        Mock(return_value=None)
    )
    result = send_push_notifications.run(
        game_id=2,
        notification_type=sample_notification.type
    )
    assert 'completed with result: None' in result
    assert push_service_enabled.process_notifications_by_type.called


def test_send_push_notifications_exception(
    monkeypatch,
    push_service_enabled,
    sample_notification
):
    """Test send_push_notifications retries on exception."""
    monkeypatch.setattr(
        push_service_enabled,
        'process_notifications_by_type',
        Mock(side_effect=Exception('fail'))
    )
    with pytest.raises(Exception) as exc_info:
        send_push_notifications.run(
            game_id=3,
            notification_type=sample_notification.type
        )
    assert 'fail' in str(exc_info.value)


def test_retry_notification_task_success(
    push_service_enabled,
    sample_notification,
    monkeypatch
):
    """Test retry_notification_task returns True on success."""
    monkeypatch.setattr(
        push_service_enabled,
        'send_notification_by_token',
        Mock(return_value=True)
    )
    result = retry_notification_task.run(
        token='token123',
        notification_type=sample_notification.type,
        game_id=42
    )
    assert result is True
    assert push_service_enabled.send_notification_by_token.called


def test_retry_notification_task_failure(
    push_service_enabled,
    sample_notification,
    monkeypatch
):
    """Test retry_notification_task returns False on failure."""
    monkeypatch.setattr(
        push_service_enabled,
        'send_notification_by_token',
        Mock(return_value=False)
    )
    result = retry_notification_task.run(
        token='token456',
        notification_type=sample_notification.type,
        game_id=99
    )
    assert result is False
    assert push_service_enabled.send_notification_by_token.called


def test_retry_notification_task_exception(
    monkeypatch,
    push_service_enabled,
    sample_notification
):
    """Test retry_notification_task retries on exception."""
    monkeypatch.setattr(
        push_service_enabled,
        'send_notification_by_token',
        Mock(side_effect=Exception('fail'))
    )
    with pytest.raises(Exception) as exc_info:
        retry_notification_task.run(
            token='token789',
            notification_type=sample_notification.type,
            game_id=77
        )
    assert 'fail' in str(exc_info.value)