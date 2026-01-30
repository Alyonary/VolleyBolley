import logging
from datetime import datetime

from celery import current_app
from celery.app.task import Task
from django.conf import settings
from kombu.exceptions import OperationalError
from redis import Redis
from redis.exceptions import ConnectionError as RedisConnectionError

from apps.core.base import BaseConnectionManager, BaseInspector
from apps.notifications.constants import (
    CELERY_INSPECTOR_TIMEOUT,
    CeleryInspectorMessages,
)

logger = logging.getLogger(__name__)


class CeleryInspector(BaseInspector):
    """Class for checking Celery workers."""

    def __init__(self):
        super().__init__(current_app)

    def check_connection(self):
        try:
            inspector = self.app.control.inspect(
                timeout=CELERY_INSPECTOR_TIMEOUT
            )
            workers_ping = inspector.ping()
            if workers_ping:
                return True
            if not workers_ping:
                logger.warning('No active Celery workers found')
                return False
        except (ConnectionError, OperationalError) as e:
            logger.error(f'Celery not ready: {str(e)}')
            return False
        except Exception as e:
            logger.warning(f'Uknown error: {str(e)}')
            return False


class RedisInspector(BaseInspector):
    """Class for checking connection with redis."""

    def __init__(self):
        super().__init__(
            app=Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
            )
        )

    def check_connection(self):
        try:
            return self.app.ping()
        except RedisConnectionError:
            logger.error(
                f'DNS Error: Host {settings.REDIS_HOST} not found. '
                'Check docker-compose or your hosts file.'
            )
            return False
        except Exception as e:
            logger.error(f'Unknown error : {e}')


class TaskManager(BaseConnectionManager):
    """Class for creating async task using workers."""

    def create_task(
        self, task: Task, eta: datetime, task_args: dict[str, int]
    ) -> dict[str, bool]:
        """Create async task using Celery Workers"""
        if not self.get_status():
            return {
                'success': False,
                'message': CeleryInspectorMessages.ERROR_CREATING_TASK,
            }
        eta = datetime.now()
        try:
            if task_args and eta:
                task.apply_async(eta=eta, kwargs=task_args)
            elif task_args and not eta:
                task.apply_async(kwargs=task_args)
            elif not task_args and eta:
                task.apply_async(eta=eta)
            else:
                task.apply_async()
            return {
                'success': True,
                'message': CeleryInspectorMessages.TASK_CREATED,
            }
        except OperationalError as e:
            logger.error(f'Error connecting with workers: {str(e)}')
            return {
                'success': False,
                'message': CeleryInspectorMessages.ERROR_CREATING_TASK,
            }
