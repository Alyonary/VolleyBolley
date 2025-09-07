import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'volleybolley.settings')

app = Celery('volleybolley')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

CELERY_BEAT_SCHEDULE = {
    'downgrade-inactive-players-every-day': {
        'task': 'apps.players.tasks.downgrade_inactive_players_task',
        'schedule': crontab(hour=1, minute=0),
    },
}