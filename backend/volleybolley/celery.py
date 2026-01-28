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
