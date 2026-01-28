import logging
from datetime import datetime

from celery import current_app

from apps.core.base import BaseSingleton
from apps.notifications.constants import (
    CELERY_INSPECTOR_TIMEOUT,
    CeleryInspectorMessages,
)

logger = logging.getLogger(__name__)


class CeleryInspector(BaseSingleton):
    """Class for checking Celery workers."""

    def __init__(self):
        self.ready = self.check_connection()

    def check_connection(self):
        try:
            inspector = current_app.control.inspect(
                timeout=CELERY_INSPECTOR_TIMEOUT
            )
            active_workers = inspector.active()
            if not active_workers:
                logger.warning('No active Celery workers found')
                return False
            logger.debug(f'Found {len(active_workers)} active Celery workers')
            return True
        except ImportError:
            logger.error('Celery is not installed')
            return False
        except Exception as e:
            logger.warning(f'Cannot connect to Celery: {str(e)}')
            return False


class TaskManager:
    """Class for creating async task using workers."""

    def __init__(self):
        self.inspector = CeleryInspector()
        self.ready = self.inspector.check_connection()

    def create_task(self, task, eta: datetime, **kwargs) -> dict[str, bool]:
        """Create async task using Celery Workers"""
        if not self.ready:
            return {
                'success': False,
                'message': CeleryInspectorMessages.TASK_CREATED,
            }
        task_data = {}
        if kwargs:
            task_data['kwargs'] = kwargs
        if eta:
            task_data['eta'] = eta
        if not task_data:
            task.apply_async()
        else:
            task.apply_async(**task_data)
        return {
            'success': True,
            'message': CeleryInspectorMessages.TASK_CREATED,
        }
