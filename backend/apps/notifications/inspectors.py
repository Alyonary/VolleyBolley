import logging
from datetime import datetime

from backend.apps.notifications.messages import (
    InfrastructureLogMessages,
)
from celery import current_app
from celery.app.task import Task
from django.conf import settings
from kombu.exceptions import OperationalError
from redis import Redis
from redis.exceptions import ConnectionError as RedisConnectionError

from apps.core.base import BaseConnectionManager, BaseInspector
from apps.notifications.constants import (
    CELERY_INSPECTOR_TIMEOUT,
)

logger = logging.getLogger(__name__)


class CeleryInspector(BaseInspector):
    """
    Inspector specialized in monitoring Celery worker availability.

    Uses the Celery control interface to ping active workers and verify
    the cluster health.
    """

    def __init__(self):
        """Initialize the inspector using the current Celery application."""
        super().__init__(current_app)

    def check_connection(self):
        """
        Ping Celery workers to verify they are active and responding.

        Returns:
            bool: True if at least one worker responds, False otherwise.
        """
        try:
            inspector = self.app.control.inspect(
                timeout=CELERY_INSPECTOR_TIMEOUT
            )
            workers_ping = inspector.ping()
            if workers_ping:
                return True
            if not workers_ping:
                logger.warning(InfrastructureLogMessages.CELERY_NO_WORKERS)
                return False
        except (ConnectionError, OperationalError) as e:
            logger.error(
                InfrastructureLogMessages.CELERY_NOT_READY.format(error=e)
            )
            return False
        except Exception as e:
            logger.warning(
                InfrastructureLogMessages.UNKNOWN_ERROR.format(error=str(e))
            )
            return False


class RedisInspector(BaseInspector):
    """
    Inspector specialized in monitoring Redis broker connectivity.

    Attributes:
        app (Redis): The Redis client instance used for health checks.
    """

    def __init__(self):
        """Initialize the Redis client with settings-defined credentials."""
        super().__init__(
            app=Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
            )
        )

    def check_connection(self):
        """
        Execute a Redis PING command to verify server availability.

        Returns:
            bool: True if Redis responds, False on connection or DNS errors.
        """
        try:
            return self.app.ping()
        except RedisConnectionError:
            logger.error(
                InfrastructureLogMessages.REDIS_DNS_ERROR.format(
                    host=settings.REDIS_HOST
                )
            )
            return False
        except Exception as e:
            logger.warning(
                InfrastructureLogMessages.REDIS_UNKNOWN_ERROR.format(
                    error=str(e)
                )
            )
            return False


class TaskManager(BaseConnectionManager):
    """
    Manager class for dispatching asynchronous tasks.

    Validates system readiness before attempting to enqueue tasks
    to ensure reliable delivery.
    """

    def create_task(
        self, task: Task, eta: datetime, task_args: dict[str, int]
    ) -> dict[str, bool]:
        """
        Safely dispatch a Celery task with specified scheduling and arguments.

        Args:
            task (Task): The Celery task instance to execute(task func name).
            eta (datetime): The scheduled time for the task.
            task_args (dict[str, int]): Keyword arguments for the task.

        Returns:
            dict: A status dictionary containing 'success' (bool)
                  and 'message' (str).
        """
        if not self.get_status():
            return {
                'success': False,
                'message': InfrastructureLogMessages.CELERY_NO_WORKERS,
            }
        try:
            task.apply_async(kwargs=task_args or {}, eta=eta)
            return {
                'success': True,
                'message': InfrastructureLogMessages.TASK_CREATED,
            }
        except OperationalError as e:
            logger.error(
                InfrastructureLogMessages.TASK_WORKER_ERROR.format(
                    error=str(e)
                )
            )
            return {
                'success': False,
                'message': InfrastructureLogMessages.TASK_ERROR.format(
                    error=str(e)
                ),
            }
