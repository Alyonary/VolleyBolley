from backend.apps.notifications.notifications import NotificationTypes
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from apps.event.models import Game, Tourney
from apps.notifications.push_service import PushService


def schedule_notifications_for_event(instance, event_type):
    """
    Schedule notifications for the event (Game or Tourney).
    Sends notifications 1 hour and 1 day before the event start time.
    """
    now = timezone.now()
    start_time = instance.start_time
    push_service = PushService()
    if not push_service:
        return 
    notify_hour = start_time - timezone.timedelta(hours=1)
    if notify_hour > now:
        PushService.process_notifications_by_type.apply_async(
            kwargs={
                'type': NotificationTypes.IN_GAME,
                'player_id': None,
                'game_id': instance.id
            },
            eta=notify_hour
        )

    notify_day = start_time - timezone.timedelta(days=1)
    if notify_day > now:
        PushService.process_notifications_by_type.apply_async(
            kwargs={
                'type': NotificationTypes.IN_GAME,
                'player_id': None,
                'game_id': instance.id
            },
            eta=notify_day
        )


@receiver(post_save, sender=Game)
def game_created_handler(sender, instance, created, **kwargs):
    if created:
        schedule_notifications_for_event(instance, event_type='game')


@receiver(post_save, sender=Tourney)
def tourney_created_handler(sender, instance, created, **kwargs):
    if created:
        schedule_notifications_for_event(instance, event_type='tourney')