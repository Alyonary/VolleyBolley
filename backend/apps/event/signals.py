from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from apps.event.models import Game, Tourney


def schedule_event_notifications(instance, event_type):
    """
    Schedule notifications for the event (Game or Tourney).
    Sends notifications 1 hour and 1 day before the event start time.
    """
    now = timezone.now()
    start_time = instance.start_time
    notify_hour = start_time - timezone.timedelta(hours=1)
    # Интегрировать после мержа пуш сервиса
    if notify_hour > now:
        pass
        # send_event_notification_task.apply_async(
        #     args=[instance.id, event_type, 'hour'],
        #     eta=notify_hour
        # )
    # notify_day = start_time - timezone.timedelta(days=1)
    if (start_time - now).days >= 1:
        pass
        # send_event_notification_task.apply_async(
        #     args=[instance.id, event_type, 'day'],
        #     eta=notify_day
        #     )

@receiver(post_save, sender=Game)
def game_created_handler(sender, instance, created, **kwargs):
    if created:
        schedule_event_notifications(instance, event_type='game')

@receiver(post_save, sender=Tourney)
def tourney_created_handler(sender, instance, created, **kwargs):
    if created:
        schedule_event_notifications(instance, event_type='tourney')