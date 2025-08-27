from django.db import models


class DeviceType(models.TextChoices):
    """Device type choices for push notifications."""
    IOS = 'ios', 'ios'
    ANDROID = 'android', 'android'


DEVICE_TOKEN_MAX_LENGTH: int = 255
RETRY_PUSH_TIME: int = 60
MAX_RETRIES: int = 3
