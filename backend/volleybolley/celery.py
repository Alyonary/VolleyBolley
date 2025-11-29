import logging
import os

from celery import Celery
from celery.schedules import crontab

logger = logging.getLogger('django.celery')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'volleybolley.settings')

app = Celery('volleybolley')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

CELERY_BEAT_SCHEDULE = {
    'delete-old-devices-every-day': {
        'task': 'apps.notifications.tasks.delete_old_devices_task',
        'schedule': crontab(hour=0, minute=0),
    },
    'downgrade-inactive-players-every-day': {
        'task': 'apps.players.tasks.downgrade_inactive_players_task',
        'schedule': crontab(hour=2, minute=0),
    },
    'create-rate-objects-and-notify-every-10-minutes': {
        'task': 'apps.notifications.tasks.send_rate_notification_task',
        'schedule': crontab(minute='*/10'),
    },
}
