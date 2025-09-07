from celery import shared_task
from django.utils import timezone

from apps.event.models import Game, Tourney
from apps.event.utils import create_event_rate_objects_and_notify


@shared_task
def create_rate_objects_and_notify():
    """
    Create PlayerEventRate objects for players in past events
    and notify them to rate the event if they haven't already.
    This task should be run periodically (every 10 min) to check for events
    """
    hour_ago = timezone.now() - timezone.timedelta(hours=1)
    create_event_rate_objects_and_notify(Game, hour_ago)
    create_event_rate_objects_and_notify(Tourney, hour_ago)
