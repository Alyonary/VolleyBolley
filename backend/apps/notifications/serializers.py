from rest_framework import serializers

from apps.notifications.models import DeviceType


class FCMTokenSerializer(serializers.Serializer):
    """Serializer for handling FCM device tokens."""
    token = serializers.CharField(required=True)
    platform = serializers.ChoiceField(
        choices=DeviceType,
        required=False
    )
