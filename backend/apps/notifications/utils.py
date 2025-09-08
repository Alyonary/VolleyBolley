import logging
from datetime import timedelta

from django.utils import timezone

from apps.notifications.models import Device

logger = logging.getLogger(__name__)


def delete_old_devices():
    """
    Delete device records created more than 270 days ago.
    """
    threshold_date = timezone.now() - timedelta(days=270)
    old_devices = Device.objects.filter(created_at__lt=threshold_date)
    count = old_devices.count()
    old_devices.delete()
    logger.info(f'Deleted {count} old device(s) older than 270 days.')
    return count