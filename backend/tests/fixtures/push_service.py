import builtins
from unittest.mock import Mock

import pytest
from pyfcm.errors import FCMError

from apps.notifications.push_service import PushService


@pytest.fixture
def push_service_enabled(mock_fcm_service_ok, monkeypatch):
    """
    Create real PushService instance with mocked connection checks.
    All services are available and working.
    """

    def mock_initialize_firebase(self):
        self.push_service = mock_fcm_service_ok
        return True

    def mock_check_fcm(self):
        return True

    def mock_check_celery_availability(self):
        return True

    monkeypatch.setattr(
        'apps.notifications.push_service.PushServiceConnector._initialize_firebase',
        mock_initialize_firebase,
    )
    monkeypatch.setattr(
        'apps.notifications.push_service.PushServiceConnector._check_fcm',
        mock_check_fcm,
    )
    monkeypatch.setattr(
        'apps.notifications.push_service.PushServiceConnector._check_celery_availability',
        mock_check_celery_availability,
    )

    service = PushService()
    # Теперь push_service уже создан, можно мокать notify
    monkeypatch.setattr(
        service.connector.push_service, 'notify', lambda *a, **kw: True
    )
    return service


@pytest.fixture
def push_service_disabled(monkeypatch, mock_fcm_service_fail):
    """
    Create real PushService instance with mocked connection checks.
    All services are unavailable.
    """
    service = Mock()
    def mock_initialize_firebase(self):
        self.push_service = mock_fcm_service_fail
        return False

    def mock_check_fcm(self):
        return False

    def mock_check_celery_availability(self):
        return False

    monkeypatch.setattr(
        'apps.notifications.push_service.PushServiceConnector._initialize_firebase',
        mock_initialize_firebase,
    )
    monkeypatch.setattr(
        'apps.notifications.push_service.PushServiceConnector._check_fcm',
        mock_check_fcm,
    )
    monkeypatch.setattr(
        'apps.notifications.push_service.PushServiceConnector._check_celery_availability',
        mock_check_celery_availability,
    )
    monkeypatch.setattr(
        service.connector.push_service, 'notify', lambda *a, **kw: False
    )
    service = PushService()
    assert service.connector.fb_available is False
    assert service.connector.celery_available is False
    return service


@pytest.fixture
def push_service_fcm_only(monkeypatch, mock_fcm_service_ok):
    """
    Create real PushService with FCM available but Celery unavailable.
    """

    def mock_initialize_firebase(self):
        self.push_service = mock_fcm_service_ok
        return True

    def mock_check_fcm(self):
        return True

    def mock_check_celery_availability(self):
        return False

    monkeypatch.setattr(
        'apps.notifications.push_service.PushServiceConnector._initialize_firebase',
        mock_initialize_firebase,
    )
    monkeypatch.setattr(
        'apps.notifications.push_service.PushServiceConnector._check_fcm',
        mock_check_fcm,
    )
    monkeypatch.setattr(
        'apps.notifications.push_service.PushServiceConnector._check_celery_availability',
        mock_check_celery_availability,
    )

    service = PushService()
    monkeypatch.setattr(
        service.connector.push_service, 'notify', lambda *a, **kw: True
    )
    assert service.connector.fb_available is True
    assert service.connector.celery_available is False
    return service


@pytest.fixture
def mock_fcm_service_ok():
    """Mock FCM service that always succeeds."""
    mock_fcm = Mock()
    mock_fcm.notify.return_value = True
    return mock_fcm


@pytest.fixture
def mock_fcm_service_fail():
    """Mock FCM service that always fails."""
    mock_fcm = Mock()
    mock_fcm.notify.side_effect = Exception('FCM service error')
    return mock_fcm


@pytest.fixture
def mock_fcm_service_token_fail():
    """Mock FCM service that always fails with token error."""
    mock_fcm = Mock()
    mock_fcm.notify.side_effect = FCMError('Invalid token')
    return mock_fcm


@pytest.fixture
def mock_tasks_import(monkeypatch):
    """Mock import of apps.notifications.tasks for Celery retry."""
    mock_retry_task = Mock()
    mock_retry_task.apply_async = Mock()

    original_import = builtins.__import__

    def mock_import_func(name, *args, **kwargs):
        if name == 'apps.notifications.tasks':
            mock_tasks = Mock()
            mock_tasks.retry_notification_task = mock_retry_task
            return mock_tasks
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, '__import__', mock_import_func)
    return mock_retry_task
