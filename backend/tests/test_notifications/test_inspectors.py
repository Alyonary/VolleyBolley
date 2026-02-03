from unittest.mock import Mock

import pytest

from apps.notifications.inspectors import (
    CeleryInspector,
    RedisInspector,
    TaskManager,
)
from apps.notifications.push_service import PushServiceConnector


@pytest.mark.django_db
class Testinspectors:
    def test_inspectors_distinct_instances(
        self, mock_redis_ok, mock_celery_ok
    ):
        """
        Check that Inspectors follows the singleton pattern.
        """
        redis_inspector = RedisInspector()
        celery_inspector = CeleryInspector()

        assert redis_inspector is RedisInspector(), (
            'RedisInspector should return the same instance'
        )
        assert celery_inspector is CeleryInspector(), (
            'CeleryInspector should return the same instance'
        )
        assert redis_inspector is not celery_inspector, (
            'Different inspectors must not share the same instance'
        )

    def test_task_manager_singleton_behavior(
        self, mock_redis_ok, mock_celery_ok
    ):
        """
        Check that TaskManager follows the singleton pattern.
        """
        manager1 = TaskManager(
            broker=RedisInspector(), worker=CeleryInspector()
        )
        manager2 = TaskManager(
            broker=RedisInspector(), worker=CeleryInspector()
        )

        assert manager1 is manager2, (
            'TaskManager should always return the same instance'
        )

    def test_singleton_thread_safety(self, mock_redis_ok, mock_celery_ok):
        """
        Check if the singleton implementation is thread-safe.
        """
        import threading

        instances = []

        def create_instance():
            instances.append(RedisInspector())

        threads = [threading.Thread(target=create_instance) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        for inst in instances:
            assert inst is instances[0], (
                'Threads should all receive the exact same instance'
            )

    def test_task_manager_and_push_service_connector_init(
        self, mock_celery_ok, mock_redis_ok
    ):
        """
        Check TaskManager and PushService connector initialization.
        Ensure different objects are created.
        """
        connector = PushServiceConnector(
            main_service=Mock(),
            worker=CeleryInspector(),
            broker=RedisInspector(),
        )
        manager = TaskManager(
            worker=CeleryInspector(), broker=RedisInspector()
        )
        assert connector is not manager
