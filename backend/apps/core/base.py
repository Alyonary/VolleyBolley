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
    Abstract base class for inspecting component connection health.

    This class serves as a singleton inspector to verify if a specific
    service (like a broker or a worker) is accessible and operational.

    Attributes:
        app (Any): The application instance or client to be inspected.
        ready (bool): The connection status determined during initialization.
    """

    def __init__(self, app: Any):
        """
        Initialize the inspector and perform an initial connection check.

        Args:
            app (Any): The application or library instance to monitor.
        """
        if self._initialized:
            return
        self.app = app
        self.ready = self.check_connection()
        super().__init__()

    def check_connection(self):
        """
        Execute the specific logic to verify service availability.

        Raises:
            NotImplementedError: Must be implemented by subclasses to define
                how to check the connection for a specific service.
        """
        raise NotImplementedError


class BaseConnectionManager(BaseSingleton):
    """
    Manages the connection status of the message broker and worker.

    Acts as a centralized interface to verify that both core components
    of the task queue system are operational.

    Attributes:
        broker (BaseInspector): Inspector instance for the message broker.
        worker (BaseInspector): Inspector instance for the worker process.
        ready (bool): Initial connection state of both components.
    """

    def __init__(self, broker: BaseInspector, worker: BaseInspector):
        """Initialize the connection manager with specific inspectors."""
        if self._initialized:
            return
        self.broker = broker
        self.worker = worker
        self.ready = self.get_status()

    def get_status(self):
        """
        Evaluate the current availability of both broker and worker.

        Returns:
            bool: True if both components are ready, False otherwise.
        """
        return self.broker.ready and self.worker.ready
