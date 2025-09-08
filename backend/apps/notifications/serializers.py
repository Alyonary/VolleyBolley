from backend.apps.notifications.notifications import Notification
from rest_framework import serializers

from apps.notifications.models import DeviceType, Notifications


class FCMTokenSerializer(serializers.Serializer):
    """Serializer for handling FCM device tokens."""
    token = serializers.CharField(required=True)
    platform = serializers.ChoiceField(
        choices=DeviceType,
        required=False
    )


class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer for Notification model.
    - GET: returns full notification info.
    - PUT: processes notification_id for marking as read.
    """

    title = serializers.SerializerMethodField()
    message = serializers.SerializerMethodField()
    screen = serializers.SerializerMethodField()
    notification_id = serializers.IntegerField(required=False)

    class Meta:
        model = Notifications
        fields = [
            'id',
            'type',
            'created_at',
            'title',
            'message',
            'screen',
            'notification_id',
        ]

    def __init__(self, *args, **kwargs):
        """
        Custom init to handle different fields for GET and PUT requests.
        """
        super().__init__(*args, **kwargs)
        if self.instance is None and self.initial_data is not None:
            self.fields.clear()
            self.fields['notification_id'] = serializers.IntegerField()

    def get_title(self, obj):
        return Notification(obj.type).title

    def get_message(self, obj):
        return Notification(obj.type).body

    def get_screen(self, obj):
        return Notification(obj.type).screen

    def update(self, instance, validated_data):
        instance.is_read = True
        instance.save()
        return instance
