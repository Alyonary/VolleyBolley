from threading import Lock
from typing import Any


class BaseSingleton:
    """Base Singleton class implementation."""

    _instance = None
    _lock = Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        self._initialized = True


class BaseInspector(BaseSingleton):
    """
    Base Inspector class.
    Implements logic for checking connections to additional resources
    such as Celery and Redis.

    Args:
        BaseSingleton (_type_): _description_
    """

    def __init__(self, app: Any):
        if self._initialized:
            return
        self.app = app
        self.ready = self.check_connection()
        super().__init__()

    def check_connection(self):
        raise NotImplementedError


class BaseConnectionManager(BaseSingleton):
    """Class check"""

    def __init__(self, broker: BaseInspector, worker: BaseInspector):
        if self._initialized:
            return
        self.broker = broker
        self.worker = worker
        self.ready = self.get_status()

    def get_status(self):
        """Get worker and broker connection status."""
        return self.broker.ready and self.worker.ready
