import builtins
from unittest.mock import Mock

import pytest

from apps.notifications import push_service as push_service_module
from apps.notifications.push_service import PushService


class MockPushServiceConnector:
    def __init__(
        self,
        main_service=None,
        fb_available=True,
        celery_available=True,
    ):
        self.main_service = main_service
        self.fb_available = fb_available
        self.celery_available = celery_available
        self.enable = fb_available and celery_available
        self._initialized = True
        self.fb_admin = Mock() if fb_available else None
        self.push_service = Mock()
        self.push_service.notify = Mock()

    def __bool__(self):
        return all(self.get_status().values())

    def get_status(self):
        return {
            'notifications_enabled': self.enable,
            'fcm_available': self.fb_available,
            'celery_available': self.celery_available,
            'initialized': self._initialized,
        }

    def reconnect(self):
        return self.enable

    def _check_fcm(self):
        return self.fb_available

    def _check_celery_availability(self):
        return self.celery_available

    def _initialize_firebase(self):
        return self.fb_available

    def _initialize_services(self):
        self.enable = self.fb_available and self.celery_available
        self._initialized = True


@pytest.fixture
def push_service_enabled(monkeypatch):
    """
    PushService с мок-коннектором: оба сервиса доступны.
    """

    def connector_factory(main_service):
        return MockPushServiceConnector(
            main_service, fb_available=True, celery_available=True
        )

    monkeypatch.setattr(
        push_service_module, 'PushServiceConnector', connector_factory
    )
    return PushService()


@pytest.fixture
def push_service_disabled(monkeypatch):
    """
    PushService с мок-коннектором: оба сервиса недоступны.
    """

    def connector_factory(main_service):
        return MockPushServiceConnector(
            main_service, fb_available=False, celery_available=False
        )

    monkeypatch.setattr(
        push_service_module, 'PushServiceConnector', connector_factory
    )
    return PushService()


@pytest.fixture
def push_service_fcm_only(monkeypatch):
    """
    PushService с мок-коннектором: только FCM доступен.
    """

    def connector_factory(main_service):
        return MockPushServiceConnector(
            main_service, fb_available=True, celery_available=False
        )

    monkeypatch.setattr(
        push_service_module, 'PushServiceConnector', connector_factory
    )
    return PushService()


@pytest.fixture
def push_service_with_celery_only(monkeypatch):
    """
    PushService с мок-коннектором: только Celery доступен.
    """

    def connector_factory(main_service):
        return MockPushServiceConnector(
            main_service, fb_available=False, celery_available=True
        )

    monkeypatch.setattr(
        push_service_module, 'PushServiceConnector', connector_factory
    )
    return PushService()


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


@pytest.fixture
def push_service_connector_all_ok(monkeypatch):
    """PushService с мок-коннектором: оба сервиса доступны."""

    def connector_factory(main_service):
        return MockPushServiceConnector(
            main_service, fb_available=True, celery_available=True
        )

    monkeypatch.setattr(
        push_service_module, 'PushServiceConnector', connector_factory
    )
    return push_service_module.PushService()


@pytest.fixture
def push_service_connector_fcm_only(monkeypatch):
    """PushService с мок-коннектором: только FCM доступен."""

    def connector_factory(main_service):
        return MockPushServiceConnector(
            main_service, fb_available=True, celery_available=False
        )

    monkeypatch.setattr(
        push_service_module, 'PushServiceConnector', connector_factory
    )
    return push_service_module.PushService()


@pytest.fixture
def push_service_connector_none(monkeypatch):
    """PushService с мок-коннектором: оба сервиса недоступны."""

    def connector_factory(main_service):
        return MockPushServiceConnector(
            main_service, fb_available=False, celery_available=False
        )

    monkeypatch.setattr(
        push_service_module, 'PushServiceConnector', connector_factory
    )
    return push_service_module.PushService()
