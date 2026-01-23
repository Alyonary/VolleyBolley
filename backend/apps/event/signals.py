from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from apps.event.models import Game, GameInvitation, Tourney, TourneyTeam
from apps.notifications.constants import NotificationTypes
from apps.notifications.models import NotificationsTime
from apps.notifications.tasks import send_event_notification_task


def schedule_event_notifications(instance, event_type):  # noqa: RET503
    """
    Schedule notifications for the event (Game or Tourney).
    Sends notifications 1 hour and 1 day before the event start time.
    """
    now = timezone.now()
    notification_type = {
        'game': NotificationTypes.GAME_REMINDER,
        'tourney': NotificationTypes.TOURNEY_REMINDER,
    }.get(
        event_type.lower(),
    )
    if not notification_type:
        return False
    start_time = instance.start_time
    pre_event_notification_time = (
        start_time - NotificationsTime.get_pre_event_time()
    )
    if pre_event_notification_time > now:
        return send_event_notification_task.apply_async(
            args=[
                instance.id,
                notification_type,
            ],
            eta=pre_event_notification_time,
        )
    advance_notification_time = (
        start_time - NotificationsTime.get_advance_notification_time()
    )
    if (start_time - now).days >= 1:
        return send_event_notification_task.apply_async(
            args=[
                instance.id,
                notification_type,
            ],
            eta=advance_notification_time,
        )
    return False


@receiver(post_save, sender=Game)
def game_created_handler(sender, instance, created, **kwargs):
    if created:
        schedule_event_notifications(instance, event_type='game')


@receiver(post_save, sender=Tourney)
def tourney_created_handler(sender, instance, created, **kwargs):
    if created:
        schedule_event_notifications(instance, event_type='tourney')


@receiver(post_save, sender=GameInvitation)
def game_invitation_created_handler(sender, instance, created, **kwargs):
    if created:
        send_event_notification_task.delay(
            instance.game.id, NotificationTypes.GAME_INVITE
        )


@receiver(post_save, sender=Tourney)
def create_tourney_teams(sender, instance, created, **kwargs):
    if created:
        if instance.maximum_teams is None and instance.is_individual:
            instance.maximum_teams = 1
        for _ in range(instance.maximum_teams):
            TourneyTeam.objects.create(tourney=instance)
