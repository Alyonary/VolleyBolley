from rest_framework import serializers

from apps.notifications.models import DeviceType, Notifications


class FCMTokenSerializer(serializers.Serializer):
    """Serializer for handling FCM device tokens."""

    token = serializers.CharField(required=True)
    platform = serializers.ChoiceField(choices=DeviceType, required=False)


class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer for Notification model.
    - GET: returns full notification info.
    - PUT: processes notification_id for marking as read.
    """

    title = serializers.CharField(
        source='notification_type.title',
        read_only=True
    )
    message = serializers.CharField(
        source='notification_type.body',
        read_only=True
    )
    screen = serializers.CharField(
        source='notification_type.screen',
        read_only=True
    )
    notification_id = serializers.IntegerField(source='id')
    event_id = serializers.SerializerMethodField()

    class Meta:
        model = Notifications
        fields = [
            'notification_id',
            'created_at',
            'title',
            'message',
            'screen',
            'event_id',
        ]

    def get_event_id(self, obj):
        if obj.game_id:
            return obj.game_id
        if obj.tourney_id:
            return obj.tourney_id
        return None

    def update(self, instance, validated_data):
        instance.is_read = True
        instance.save()
        return instance
