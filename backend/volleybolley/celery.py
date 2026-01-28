import logging
import os
from datetime import datetime
from threading import Lock

from celery import Celery, current_app
from celery.schedules import crontab

from apps.core.constants import CeleryInspectorMessages

logger = logging.getLogger('django.celery')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'volleybolley.settings')

app = Celery('volleybolley')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()
INSPECTOR_TIMEOUT: float = 2.0
CELERYBEAT_SCHEDULE = {
    'delete-old-devices-every-day': {
        'task': 'apps.notifications.tasks.delete_old_devices_task',
        'schedule': crontab(hour=0, minute=0),
    },
    'downgrade-inactive-players-every-day': {
        'task': 'apps.players.tasks.downgrade_inactive_players_task',
        'schedule': crontab(hour=2, minute=0),
    },
    'tourneys-rate-objects-and-notify-every-10-minutes': {
        'task': 'apps.notifications.tasks.send_rate_tourney_notification_task',
        'schedule': crontab(minute='*/10'),
    },
    'games-create-rate-objects-and-notify-every-10-minutes': {
        'task': 'apps.notifications.tasks.send_rate_game_notification_task',
        'schedule': crontab(minute='*/10'),
    },
    'collect-stats-for-previous-day-every-day': {
        'task': 'apps.core.task.collect_stats_for_previous_day_task',
        'schedule': crontab(hour=5, minute=0),
    },
}


class CeleryInspector:
    """Class for checking Celery workers and creating task."""

    _instance = None
    _lock = Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.ready = self.check_connection()

    def check_connection(self):
        try:
            inspector = current_app.control.inspect(timeout=INSPECTOR_TIMEOUT)
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

    def delay_task(
        self, task, task_args: dict[str, int, bool] | None
    ) -> dict[str, bool]:
        if not self.ready:
            return {
                'success': False,
                'message': CeleryInspectorMessages.WORKERS_NOT_READY,
            }
        if not task_args:
            task.delay()
        else:
            task.delay(**task_args)
        return {
            'success': True,
            'message': CeleryInspectorMessages.TASK_CREATED,
        }

    def apply_async_task(
        self, task, eta: datetime, *args
    ) -> dict[str, bool]:
        if not self.ready:
            return {
                'success': False,
                'message': CeleryInspectorMessages.TASK_CREATED,
            }
        task_data = {}
        if args:
            task_data['args'] = args
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
