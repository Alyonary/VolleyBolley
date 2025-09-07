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
        'schedule': crontab(hour=2, minute=0),
    },
    'create-rate-objects-and-notify-every-10-minutes': {
        'task': 'apps.event.tasks.create_rate_objects_and_notify',
        'schedule': crontab(minute='*/10'),
    },
    'update-players-rating-every-day': {
        'task': 'apps.players.tasks.update_players_rating_task',
        'schedule': crontab(hour=1, minute=0),
    },
}