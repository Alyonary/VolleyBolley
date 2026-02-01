import builtins
from unittest.mock import Mock

import pytest

from apps.notifications import push_service as push_service_module
from apps.notifications import task_manager as inspectors_module
from apps.notifications.messages import PushServiceMessages
from apps.notifications.push_service import PushService


def create_mock_push_service_with_connectors(
    monkeypatch, fb_available: bool, celery_available: bool
) -> PushService:
    """
    Creates a PushService instance with mocked connectors and inspectors.

    Args:
        monkeypatch: Pytest's monkeypatch fixture.
        fb_available (bool): Mocked availability status for Firebase.
        celery_available (bool): Mocked availability status for Celery/Redis.

    Returns:
        PushService: An initialized service instance with mocked dependencies.
    """

    def connector_factory(main_service, worker, broker):
        return MockPushServiceConnector(
            main_service,
            fb_available=fb_available,
            celery_available=celery_available,
        )

    def inspector_factory():
        return MockInspector(status=celery_available)

    monkeypatch.setattr(
        inspectors_module, 'CeleryInspector', inspector_factory
    )
    monkeypatch.setattr(inspectors_module, 'RedisInspector', inspector_factory)

    monkeypatch.setattr(
        push_service_module, 'PushServiceConnector', connector_factory
    )
    return PushService()


class MockInspector:
    """
    Mock object for checking external service health (Celery, Redis, etc.).

    Attributes:
        ready (bool): The readiness status of the service.
    """

    def __init__(self, status: bool):
        self.app = Mock()
        self.ready = status

    def check_connection(self):
        """Returns the connection readiness status."""
        return self.ready


class MockPushServiceConnector:
    """
    Mock connector that simulates Firebase and Celery integration logic.

    Manages service availability states and initialization for testing.
    """

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
        self.fb_admin = Mock() if fb_available else None
        self.push_service = Mock()
        self.push_service.notify = Mock()

    def __bool__(self):
        """Returns True if all required backend services are available."""
        return all(self.get_status().values())

    def get_status(self):
        """Returns a detailed status mapping of all components."""
        return {
            'notifications_enabled': self.enable,
            'fcm_available': self.fb_available,
            'celery_available': self.celery_available,
        }

    def reconnect(self):
        """Simulates a service reconnection attempt."""
        return self.enable

    def _check_fcm(self):
        """Checks Firebase Cloud Messaging availability."""
        return self.fb_available

    def _check_celery_availability(self):
        """Checks if Celery workers are ready."""
        return self.celery_available

    def _initialize_firebase(self):
        """Simulates Firebase Admin SDK initialization."""
        return self.fb_available

    def _initialize_services(self):
        """Initializes internal connector services."""
        self.enable = self.fb_available and self.celery_available
        self._initialized = True


@pytest.fixture
def push_service_enabled(monkeypatch):
    """Fixture for PushService with both Firebase and Celery enabled."""
    return create_mock_push_service_with_connectors(monkeypatch, True, True)


@pytest.fixture
def push_service_disabled(monkeypatch):
    """Fixture for PushService with both services unavailable."""
    return create_mock_push_service_with_connectors(monkeypatch, False, False)


@pytest.fixture
def push_service_fcm_only(monkeypatch):
    """Fixture for PushService where only Firebase is ready."""
    return create_mock_push_service_with_connectors(monkeypatch, True, False)


@pytest.fixture
def push_service_with_celery_only(monkeypatch):
    """Fixture for PushService where only Celery is ready."""
    return create_mock_push_service_with_connectors(monkeypatch, False, True)


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


@pytest.fixture
def push_service_answer_sample() -> dict[str | int | bool]:
    return PushServiceMessages.ANSWER_SAMPLE.keys()
