from abc import ABCMeta, abstractmethod
from threading import Lock
from typing import Any


class SingletonMeta(ABCMeta):
    """
    A thread-safe implementation of the Singleton pattern.

    Ensures that only one instance of the class exists in the application
    context, using a double-checked locking mechanism.
    """

    _instances = {}
    _lock = Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]


class BaseInspector(metaclass=SingletonMeta):
    """
    Abstract base class for inspecting component connection health.

    This class defines the interface for service-specific inspectors
    (e.g., brokers, databases, workers). It ensures that connection
    logic is implemented in subclasses.

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
        self.app = app
        self.ready = self.check_connection()
        self._initialized = True

    @abstractmethod
    def check_connection(self) -> bool:
        """
        Execute the specific logic to verify service availability.

        Returns:
            bool: True if the service is reachable, False otherwise.

        Note:
            This method must be overridden by concrete subclasses.
        """


class BaseConnectionManager(metaclass=SingletonMeta):
    """
    Manages and aggregates the connection status of system components.

    Acts as a centralized interface to verify that all core components
    (like brokers and workers) are operational.

    Attributes:
        broker (BaseInspector): Inspector instance for the message broker.
        worker (BaseInspector): Inspector instance for the worker process.
        ready (bool): Combined health status of all monitored components.
    """

    def __init__(self, broker: BaseInspector, worker: BaseInspector):
        """
        Initialize the connection manager with specific component inspectors.

        Args:
            broker (BaseInspector): An inspector instance for the broker.
            worker (BaseInspector): An inspector instance for the worker.
        """
        self.broker = broker
        self.worker = worker
        self.ready = self.get_status()
        self._initialized = True

    def get_status(self) -> bool:
        """
        Evaluate the current availability of all registered components.

        Returns:
            bool: True if all components are ready, False otherwise.
        """
        return self.broker.ready and self.worker.ready
