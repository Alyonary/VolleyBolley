import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'volleybolley.settings')

app = Celery('volleybolley')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()


CELERY_BEAT_SCHEDULE = {
    'delete-old-devices-every-day': {
        'task': 'apps.notifications.tasks.delete_old_devices_task',
        'schedule': crontab(hour=0, minute=0),
    },
}
