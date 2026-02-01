from random import choice

import pytest

from apps.event.models import Game, Tourney
from apps.notifications.constants import NotificationTypes
from apps.notifications.messages import PushServiceMessages
from apps.notifications.models import Device, Notifications, NotificationsBase
from apps.notifications.push_service import PushService
from apps.notifications.tasks import (
    inform_removed_players_task,
    send_event_notification_task,
    send_invite_to_player_task,
)
from apps.players.models import Player


@pytest.mark.django_db
class TestNotificationTasks:
    """Tests for notification-related Celery tasks."""

    @pytest.mark.parametrize(
        'notification_type, event_type',
        [
            (NotificationTypes.GAME_REMINDER, 'game'),
            (NotificationTypes.GAME_RATE, 'game'),
            (NotificationTypes.TOURNEY_REMINDER, 'tourney'),
            (NotificationTypes.TOURNEY_RATE, 'tourney'),
        ],
    )
    def test_send_event_reminder_task_success(
        self,
        push_service_enabled: PushService,
        game_thailand: Game,
        tourney_thailand: Tourney,
        players_with_devices: Player,
        all_notification_types: NotificationsBase,
        push_service_answer_sample: dict,
        event_type: str,
        notification_type: str,
    ):
        """Test send_push_notifications task success."""
        if event_type == 'game':
            event = game_thailand
            qs_data = {'game': game_thailand}
        else:
            event = tourney_thailand
            qs_data = {'tourney': tourney_thailand}
        event.players.set(players_with_devices)
        result = send_event_notification_task.run(
            event_id=event.id,
            notification_type=notification_type,
        )
        for p in players_with_devices:
            qs_data['player'] = p
            qs_data['notification_type'] = all_notification_types[
                notification_type
            ]
            notif_in_db = Notifications.objects.filter(**qs_data).first()
            assert notif_in_db is not None
        assert isinstance(result, dict)
        assert all(
            list(map(lambda k: k in push_service_answer_sample, result))
        )
        assert result['success'] is True
        assert result['notification_type'] == notification_type
        assert result['message'] == PushServiceMessages.SUCCESS

    def test_send_game_reminder_error(
        self,
        push_service_disabled: PushService,
        game_thailand: Game,
        players_with_devices: Player,
        all_notification_types: NotificationsBase,
        push_service_answer_sample: dict,
    ):
        """Test send_push_notifications task success."""
        game_thailand.players.set(players_with_devices)
        result = send_event_notification_task.run(
            event_id=game_thailand.id,
            notification_type=NotificationTypes.GAME_REMINDER,
        )
        for p in players_with_devices:
            notif_in_db = Notifications.objects.filter(
                player=p,
                game=game_thailand,
            ).first()
            assert notif_in_db is None
        assert isinstance(result, dict)
        assert all(
            list(map(lambda k: k in push_service_answer_sample, result))
        )
        assert result['success'] is False
        assert result['message'] == PushServiceMessages.SERVICE_UNAVAILABLE

    @pytest.mark.parametrize(
        'notification_type, event_type',
        [
            (
                NotificationTypes.GAME_REMOVED,
                'game',
            ),
            (NotificationTypes.TOURNEY_REMOVED, 'tourney'),
        ],
    )
    def test_inform_removed_players_task_success(
        self,
        push_service_enabled: PushService,
        sample_device: Device,
        game_thailand: Game,
        notification_type: str,
        event_type: str,
        all_notification_types: NotificationsBase,
        push_service_answer_sample: dict,
    ):
        """Test send_push_notifications task success."""
        player = sample_device.player
        result = inform_removed_players_task.run(
            event_id=game_thailand.id,
            player_id=player.id,
            event_type=event_type,
        )
        assert isinstance(result, dict)
        assert all(
            list(map(lambda k: k in push_service_answer_sample, result))
        )
        assert result['success'] is True
        assert result['message'] == PushServiceMessages.SUCCESS
        assert result['notification_type'] == notification_type

    @pytest.mark.parametrize(
        'notification_type,',
        [
            NotificationTypes.GAME_INVITE,
            NotificationTypes.TOURNEY_INVITE,
        ],
    )
    def test_send_invite_to_player_task_success(
        self,
        push_service_enabled: PushService,
        game_thailand: Game,
        tourney_thailand: Tourney,
        players_with_devices: list[Player],
        notification_type: str,
        all_notification_types: NotificationsBase,
        push_service_answer_sample: dict,
    ):
        """Test send_push_notifications task success."""
        player: Player = choice(players_with_devices)
        if notification_type in NotificationTypes.FOR_TOURNEYS:
            qs_data = {
                'tourney': tourney_thailand,
            }
            event = tourney_thailand
        else:
            event = game_thailand
            qs_data = {
                'game': game_thailand,
            }
        qs_data['player'] = player
        qs_data['notification_type'] = all_notification_types[
            notification_type
        ]
        event.players.set(players_with_devices)
        result = send_invite_to_player_task.run(
            player_id=player.id,
            event_id=event.id,
            notification_type=notification_type,
        )
        notif_in_db = Notifications.objects.filter(**qs_data).first()
        assert notif_in_db is not None
        assert isinstance(result, dict)
        assert all(
            list(map(lambda k: k in push_service_answer_sample, result))
        )
        assert result['success'] is True
        assert result['notification_type'] == notification_type
        assert result['message'] == PushServiceMessages.SUCCESS
