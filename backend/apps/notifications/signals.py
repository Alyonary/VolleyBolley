from django.db.models.signals import post_migrate
from django.dispatch import receiver

from apps.core.signals import table_exists
from apps.notifications.utils import initialize_notification_time_settings


@receiver(post_migrate)
def create_notification_time_settings(sender, **kwargs):
    """
    Ensure only one NotificationTime instance exists.
    If a new instance is created, delete all other instances.
    """
    if table_exists('notifications_notificationstime'):
        initialize_notification_time_settings()
