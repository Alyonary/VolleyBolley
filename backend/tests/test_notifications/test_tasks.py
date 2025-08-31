from unittest.mock import Mock

from apps.notifications.tasks import (
    retry_notification_task,
    send_push_notifications,
)


def test_send_push_notifications_success(mock_push_service):
    """Test send_push_notifications task success."""
    mock_push_service.process_notifications_by_type.return_value = {
        'successful': 2
    }
    result = send_push_notifications.run(
        game_id=1,
        notification_type='joinGame'
    )
    assert 'completed with result:' in result
    assert mock_push_service.process_notifications_by_type.called


def test_send_push_notifications_none(mock_push_service):
    """Test send_push_notifications task returns None result."""
    mock_push_service.process_notifications_by_type.return_value = None
    result = send_push_notifications.run(
        game_id=2,
        notification_type='rate'
    )
    assert 'completed with result: None' in result
    assert mock_push_service.process_notifications_by_type.called


def test_send_push_notifications_exception(
    monkeypatch,
    mock_push_service
):
    """Test send_push_notifications retries on exception."""
    mock_self = Mock()
    mock_self.retry = Mock()
    mock_push_service.process_notifications_by_type.side_effect = Exception(
        'fail'
    )
    send_push_notifications(
        mock_self,
        game_id=3,
        notification_type='removed'
    )
    assert mock_self.retry.called


def test_retry_notification_task_success(
    mock_push_service,
    mock_notification
):
    """Test retry_notification_task returns True on success."""
    mock_push_service.send_notification_by_token.return_value = True
    result = retry_notification_task.run(
        token='token123',
        notification_type='rate',
        game_id=42
    )
    assert result is True
    assert mock_push_service.send_notification_by_token.called


def test_retry_notification_task_failure(
    mock_push_service,
    mock_notification
):
    """Test retry_notification_task returns False on failure."""
    mock_push_service.send_notification_by_token.return_value = False
    result = retry_notification_task.run(
        token='token456',
        notification_type='removed',
        game_id=99
    )
    assert result is False
    assert mock_push_service.send_notification_by_token.called


def test_retry_notification_task_exception(
    monkeypatch,
    mock_push_service,
    mock_notification
):
    """Test retry_notification_task retries on exception."""
    mock_self = Mock()
    mock_self.retry = Mock()
    mock_push_service.send_notification_by_token.side_effect = Exception(
        'fail'
    )
    retry_notification_task(
        mock_self,
        token='token789',
        notification_type='joinGame',
        game_id=77
    )