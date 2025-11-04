from rest_framework import serializers
from rest_framework.exceptions import ValidationError

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
    body = serializers.CharField(
        source='notification_type.body',
        read_only=True
    )
    screen = serializers.CharField(
        source='notification_type.screen',
        read_only=True
    )
    notification_id = serializers.PrimaryKeyRelatedField(
        source='id', queryset=Notifications.objects.all()
    )
    event_id = serializers.SerializerMethodField(read_only=True)
    date = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Notifications
        fields = [
            'screen',
            'notification_id',
            'event_id',
            'date',
            'title',
            'body',
        ]

    def get_event_id(self, obj):
        if obj.game_id:
            return obj.game_id
        if obj.tourney_id:
            return obj.tourney_id
        return None

    def get_date(self, obj):
        return obj.created_at.date()

    def update(self, instance, validated_data):
        instance.is_read = True
        instance.save()
        return instance

    def validate(self, attrs):
        player = self.context.get('player')
        notification = attrs.get('id')
        if not notification:
            raise ValidationError(
                'Notification does not exist'
            )
        if notification.player != player:
            raise ValidationError(
                f'Notification {notification.id} does not belong'
                f' to player {player.id}'
            )
        return super().validate(attrs)

    def save(self, **kwargs):
        return super().save(**kwargs)


class NotificationListSerializer(serializers.Serializer):
    """Serializer for notification list.

    Verify, serialize and deserialize data.
    """
    notifications = serializers.ListField(child=NotificationSerializer())
