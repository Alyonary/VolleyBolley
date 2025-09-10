import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.notifications.models import Notifications
from apps.notifications.notifications import NotificationTypes
from apps.players.models import Player


@pytest.mark.django_db
class TestNotificationsModel:
    def test_create_notification(self, in_game_notification, players):
        """Test creating a notification."""
        player = players['player1']
        notif = Notifications.objects.create(
            player=player, type=in_game_notification.type
        )
        assert notif.id is not None
        assert notif.is_read is False
        assert notif.type == in_game_notification.type
        assert notif.player == player

    def test_is_read_default_false(self, players):
        """Test that is_read defaults to False."""
        player = players['player1']
        notif = Notifications.objects.create(
            player=player, type=NotificationTypes.RATE, is_read=True
        )
        assert notif.id is not None
        assert notif.is_read is False

    def test_str_representation(self, users):
        """Test the string representation of the Notifications model."""
        user = users['user1']
        player = Player.objects.create(user=user)
        notif = Notifications.objects.create(player=player, type='rate')
        notif2 = Notifications.objects.create(player=player, type='removed')
        notif3 = Notifications.objects.create(player=player, type='InGame')
        assert str(notif) == f'Notification rate for {user.username}'
        assert str(notif2) == f'Notification removed for {user.username}'
        assert str(notif3) == f'Notification InGame for {user.username}'

    @pytest.mark.parametrize(
        'notif_type', [choice for choice, _ in NotificationTypes.CHOICES]
    )
    def test_notification_type_choices_param(self, players, notif_type):
        """Test that all notification types can be created."""
        player = players['player1']
        notif = Notifications.objects.create(player=player, type=notif_type)
        assert notif.type == notif_type

    def test_invalid_notification_type(self, players):
        """Test a notification with an invalid type raises an error."""
        player = players['player1']
        notif = Notifications.objects.create(
            player=player, type='invalid_type'
        )
        with pytest.raises(ValidationError):
            notif.full_clean()

    def test_created_at_auto_now_add(self, players):
        """Test that created_at is automatically set on creation."""
        player = players['player1']
        notif = Notifications.objects.create(
            player=player, type=NotificationTypes.RATE
        )
        assert notif.created_at is not None
        assert abs((timezone.now() - notif.created_at).total_seconds()) < 5
