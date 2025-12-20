import logging
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.notifications.constants import (
    DEV_NOTIFICATION_TIME,
    FCM_TOKEN_EXPIRY_DAYS,
    PROD_NOTIFICATION_TIME,
)
from apps.notifications.models import Device, NotificationsTime

logger = logging.getLogger(__name__)


def delete_old_devices():
    """
    Delete device records created more than 270 days ago.
    """
    threshold_date = timezone.now() - timedelta(days=FCM_TOKEN_EXPIRY_DAYS)
    old_devices = Device.objects.filter(created_at__lt=threshold_date)
    count = old_devices.count()
    old_devices.delete()
    logger.info(f'Deleted {count} old device(s) older than 270 days.')
    return count


def initialize_notification_time_settings() -> None:
    with transaction.atomic():
        if not NotificationsTime.objects.exists():
            for preset in [
                DEV_NOTIFICATION_TIME,
                PROD_NOTIFICATION_TIME,
            ]:
                NotificationsTime.objects.get_or_create(
                    name=preset.name,
                    defaults={
                        'closed_event_notification': preset.closed_event,
                        'pre_event_notification': preset.pre_event,
                        'advance_notification': preset.advance,
                        'is_active': preset.is_active,
                    },
                )
            logger.info('Initialized notification time settings.')
        else:
            logger.info('Notification time settings already initialized.')
