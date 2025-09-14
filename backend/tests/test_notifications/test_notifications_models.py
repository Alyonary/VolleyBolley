import pytest
from django.db import IntegrityError
from django.utils import timezone

from apps.notifications.constants import (
    NOTIFICATION_INIT_DATA,
    NotificationTypes,
)
from apps.notifications.models import Notifications, NotificationsBase


@pytest.mark.django_db
class TestNotificationsModel:
    def test_create_notification(self, in_game_notification_type, players):
        """Test creating a notification."""
        player = players['player1']
        notif = Notifications.objects.create(
            player=player, notification_type=in_game_notification_type
        )
        assert notif.id is not None
        assert notif.is_read is False
        assert notif.notification_type == in_game_notification_type
        assert notif.player == player

    def test_is_read_default_false(self, players, rate_notification_type):
        """Test that is_read defaults to False."""
        player = players['player1']
        notif = Notifications.objects.create(
            player=player,
            notification_type=rate_notification_type,
            is_read=True
        )
        assert notif.id is not None
        assert notif.is_read is False

    @pytest.mark.parametrize(
        'notif_type', list(NOTIFICATION_INIT_DATA.keys())
    )
    def test_notification_type_choices_param(
        self,
        players,
        all_notification_types,
        notif_type
    ):
        """
        Test that all notification types fixture.
        Test creating notifications with each type.
        """
        player = players['player1']
        notification_type_obj = all_notification_types[notif_type]
        notif = Notifications.objects.create(
            player=player,
            notification_type=notification_type_obj
        )
        assert notif.notification_type == notification_type_obj
        assert notif.notification_type.type == notif_type

    def test_created_at_auto_now_add(self, players):
        """Test created_at is set on creation."""
        player = players['player1']
        notif = Notifications.objects.create(
            player=player, notification_type=NotificationTypes.RATE
        )
        assert notif.created_at is not None
        assert abs((timezone.now() - notif.created_at).total_seconds()) < 5


@pytest.mark.django_db
class TestNotificationsBaseModel:
    def test_fields_from_fixture(
        self, rate_notification, remove_notification, in_game_notification
    ):
        """Test NotificationsBase fields from fixtures."""
        assert rate_notification.type == NotificationTypes.RATE
        assert rate_notification.title == NOTIFICATION_INIT_DATA[
            NotificationTypes.RATE]['title']
        assert rate_notification.body == NOTIFICATION_INIT_DATA[
            NotificationTypes.RATE]['body']
        assert rate_notification.screen == NOTIFICATION_INIT_DATA[
            NotificationTypes.RATE]['screen']

        assert remove_notification.type == NotificationTypes.REMOVED_GAME
        assert remove_notification.title == NOTIFICATION_INIT_DATA[
            NotificationTypes.REMOVED_GAME]['title']
        assert remove_notification.body == NOTIFICATION_INIT_DATA[
            NotificationTypes.REMOVED_GAME]['body']
        assert remove_notification.screen == NOTIFICATION_INIT_DATA[
            NotificationTypes.REMOVED_GAME]['screen']

        assert in_game_notification.type == NotificationTypes.IN_GAME
        assert in_game_notification.title == NOTIFICATION_INIT_DATA[
            NotificationTypes.IN_GAME]['title']
        assert in_game_notification.body == NOTIFICATION_INIT_DATA[
            NotificationTypes.IN_GAME]['body']
        assert in_game_notification.screen == NOTIFICATION_INIT_DATA[
            NotificationTypes.IN_GAME]['screen']

    def test_unique_type_constraint(self, rate_notification):
        """Test unique constraint on type field."""
        with pytest.raises(IntegrityError):
            NotificationsBase.objects.create(
                notification_type=NotificationTypes.RATE,
                title='Duplicate Rate',
                body='Duplicate body',
                screen='rate'
            )

    def test_initial_data_population(self):
        """Test that NOTIFICATION_INIT_DATA populates the database."""
        NotificationsBase.objects.all().delete()
        assert NotificationsBase.objects.count() == 0
        NotificationsBase.create_initial_types()
        assert NotificationsBase.objects.count() == len(NOTIFICATION_INIT_DATA)
        for notif_type, data in NOTIFICATION_INIT_DATA.items():
            obj = NotificationsBase.objects.get(notification_type=notif_type)
            assert obj.title == data['title']
            assert obj.body == data['body']
            assert obj.screen == data['screen']
