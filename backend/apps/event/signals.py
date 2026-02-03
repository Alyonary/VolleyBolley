from backend.apps.notifications.inspectors import TaskManager
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from apps.event.models import Game, GameInvitation, Tourney
from apps.notifications.constants import NotificationTypes
from apps.notifications.models import NotificationsTime
from apps.notifications.tasks import (
    send_event_notification_task,
    send_invite_to_player_task,
)


def schedule_event_notifications(instance, event_type):
    """
    Schedule notifications for the event (Game or Tourney).
    Sends notifications 1 hour and 1 day before the event start time.
    """
    task_manager = TaskManager()
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
        task_manager.create_task(
            task=send_event_notification_task,
            eta=pre_event_notification_time,
            event_id=instance.id,
            notification_type=notification_type,
        )
    advance_notification_time = (
        start_time - NotificationsTime.get_advance_notification_time()
    )
    if (start_time - now).days >= 1:
        task_manager.create_task(
            task=send_event_notification_task,
            eta=advance_notification_time,
            event_id=instance.id,
            notification_type=notification_type,
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
def game_invitation_created_handler(
    sender, instance: GameInvitation, created, **kwargs
):
    if created:
        manager = TaskManager()
        manager.create_task(
            send_invite_to_player_task,
            player_id=instance.invited.id,
            event_id=instance.game.id,
            notification_type=NotificationTypes.GAME_INVITE,
        )


# @receiver(post_save, sender=TourneyInvitation)
# def tourney_invitation_created_handler(sender, instance, created, **kwargs):
#     if created:
#         send_event_notification_task.delay(
#             instance.invited.id,
#             instance.tourney.id,
#             NotificationTypes.TOURNEY_INVITE
#         )
