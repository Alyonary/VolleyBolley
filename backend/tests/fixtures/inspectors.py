import pytest

from apps.notifications.inspectors import CeleryInspector, RedisInspector


@pytest.fixture
def mock_redis_ok(monkeypatch):
    """
    Simulate a success Redis connection: check_connection return True.
    """
    monkeypatch.setattr(RedisInspector, 'check_connection', lambda self: True)


@pytest.fixture
def mock_redis_fail(monkeypatch):
    """
    Simulate a Redis connection failure: check_connection return False.
    """
    monkeypatch.setattr(RedisInspector, 'check_connection', lambda self: False)


@pytest.fixture
def mock_celery_ok(monkeypatch):
    """
    Simulate active Celery workers: check_connection return True.
    """
    monkeypatch.setattr(CeleryInspector, 'check_connection', lambda self: True)


@pytest.fixture
def mock_celery_fail(monkeypatch):
    """
    Simulate a Celery worker: check_connection return False.
    """
    monkeypatch.setattr(
        CeleryInspector, 'check_connection', lambda self: False
    )
