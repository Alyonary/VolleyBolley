import builtins
from unittest.mock import Mock

import pytest
from pyfcm.errors import FCMError

from apps.notifications.push_service import PushService


@pytest.fixture
def reset_push_service(auto_use=True):
    """Reset PushService singleton before and after each test."""
    original_instance = PushService._instance
    PushService._instance = None
    yield
    PushService._instance = original_instance


@pytest.fixture
def push_service_enabled(reset_push_service,mock_fcm_service_ok, monkeypatch):
    """
    Create real PushService instance with mocked connection checks.
    All services are available and working.
    """

    def mock_check_fcm_file(self):
        return True
    
    def mock_check_celery_availability(self):
        return True
    

    monkeypatch.setattr(
        PushService,
        '_check_fcm_file',
        mock_check_fcm_file
    )
    monkeypatch.setattr(
        PushService,
        '_check_celery_availability',
        mock_check_celery_availability
    )

    service = PushService()
    service.push_service = mock_fcm_service_ok
    assert service.push_service is mock_fcm_service_ok
    return service


@pytest.fixture
def push_service_disabled(reset_push_service, monkeypatch):
    """
    Create real PushService instance with mocked connection checks.
    All services are unavailable.
    """
    def mock_check_fcm_file(self):
        return False

    def mock_check_celery_availability(self):
        return False

    
    monkeypatch.setattr(PushService, '_check_fcm_file', mock_check_fcm_file)
    monkeypatch.setattr(
        PushService,
        '_check_celery_availability',
        mock_check_celery_availability
    )

    service = PushService()
    
    return service


@pytest.fixture
def push_service_fcm_only(reset_push_service, monkeypatch):
    """
    Create real PushService with FCM available but Celery unavailable.
    """
    def mock_check_fcm_file(self):
        return True
    
    def mock_check_celery_availability(self):
        return False
    
    mock_fcm_instance = Mock()
    mock_fcm_instance.notify.return_value = None
    
    def mock_fcm_notification(*args, **kwargs):
        return mock_fcm_instance
    
    monkeypatch.setattr(PushService, '_check_fcm_file', mock_check_fcm_file)
    monkeypatch.setattr(
        PushService,
        '_check_celery_availability',
        mock_check_celery_availability
    )
    monkeypatch.setattr(
        'apps.notifications.push_service.FCMNotification',
        mock_fcm_notification
    )
    service = PushService()

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
    mock_fcm.notify.side_effect =  Exception("FCM service error")
    return mock_fcm


@pytest.fixture
def mock_fcm_service_token_fail():
    """Mock FCM service that always fails."""
    mock_fcm = Mock()
    mock_fcm.notify.side_effect =  FCMError("Invalid token")
    return mock_fcm


@pytest.fixture
def mock_celery_inspector_active():
    """Mock active Celery inspector."""
    mock_inspector = Mock()
    mock_inspector.active.return_value = {
        'worker1@hostname': [],
        'worker2@hostname': []
    }
    return mock_inspector


@pytest.fixture
def mock_celery_inspector_inactive():
    """Mock inactive Celery inspector."""
    mock_inspector = Mock()
    mock_inspector.active.return_value = {}
    return mock_inspector


@pytest.fixture
def push_service_mock(mocker):
    """
    Legacy fixture using pytest-mock.
    Provides complete mock of PushService class.
    """
    return mocker.patch('apps.notifications.push_service.PushService')


@pytest.fixture
def push_service_instance_mock(push_service_mock):
    """Legacy fixture providing mock instance."""
    mock_instance = Mock()
    mock_instance.enable = True
    mock_instance.send_notification_by_token.return_value = True
    push_service_mock.return_value = mock_instance
    return mock_instance


@pytest.fixture
def mock_tasks_import(monkeypatch):
    '''Mock import of apps.notifications.tasks for Celery retry.'''
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