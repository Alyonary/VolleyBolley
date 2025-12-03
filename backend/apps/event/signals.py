from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from apps.event.models import Game, GameInvitation, Tourney, TourneyTeam
from apps.notifications.constants import NotificationTypes
from apps.notifications.push_service import PushService
from apps.notifications.tasks import send_event_notification_task


def schedule_event_notifications(instance, event_type):
    """
    Schedule notifications for the event (Game or Tourney).
    Sends notifications 1 hour and 1 day before the event start time.
    """
    push_service = PushService()
    if not push_service.enable:
        return False
    now = timezone.now()
    notification_type = {
        'game': NotificationTypes.GAME_REMINDER,
        'tourney': NotificationTypes.TOURNEY_REMINDER
    }.get(event_type.lower(),)
    if not notification_type:
        return False
    start_time = instance.start_time
    notify_hour = start_time - timezone.timedelta(hours=1)
    if notify_hour > now:
        send_event_notification_task.apply_async(
            args=[instance.id, notification_type,],
            eta=notify_hour
        )
    notify_day = start_time - timezone.timedelta(days=1)
    if (start_time - now).days >= 1:
        send_event_notification_task.apply_async(
            args=[instance.id, notification_type,],
            eta=notify_day
            )


@receiver(post_save, sender=Game)
def game_created_handler(sender, instance, created, **kwargs):
    if created:
        schedule_event_notifications(instance, event_type='game')


@receiver(post_save, sender=Tourney)
def tourney_created_handler(sender, instance, created, **kwargs):
    if created:
        schedule_event_notifications(instance, event_type='tourney')


@receiver(post_save, sender=GameInvitation)
def tourney_invitation_created_handler(sender, instance, created, **kwargs):
    if created:
        event = instance.content_object  # Game or Tourney
        if isinstance(event, Game):
            # send_event_notification_task.delay(
            #     event.id,
            #     NotificationTypes.GAME_INVITE
            # )
            pass
        elif isinstance(event, Tourney):
            # send_event_notification_task.delay(
            #     event.id,
            #     NotificationTypes.TOURNEY_INVITE
            # )
            pass
        else:
            raise Exception(
                f'{isinstance} - not an invitation to a game or tournament.'
            )


@receiver(post_save, sender=Tourney)
def create_tourney_teams(sender, instance, created, **kwargs):
    if created:
        if instance.maximum_teams is None and instance.is_individual:
            instance.maximum_teams = 1
        for _ in range(instance.maximum_teams):
            TourneyTeam.objects.create(tourney=instance)
