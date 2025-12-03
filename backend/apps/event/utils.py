from datetime import datetime, timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response

from apps.event.models import Game, Tourney
from apps.notifications.constants import NotificationTypes
from apps.notifications.tasks import send_event_notification_task
from apps.players.models import Player
from apps.players.serializers import (
    PlayerRateSerializer,
    PlayerShortSerializer,
)


def process_rate_players_request(self, request, *args, **kwargs) -> Response:
    """
    Handles player rating in an event (Game or Tourney).

    GET: Returns a list of players available for rating.
    POST: Accepts ratings for players and saves them.
    """
    rater_player: Player = request.user.player
    event = self.get_object()
    if self.request.method == 'GET':
        valid_players = rater_player.get_players_to_rate(event)
        serializer = PlayerShortSerializer(valid_players, many=True)
        return Response(
            {"players": serializer.data}, status=status.HTTP_200_OK
        )

    serializer = PlayerRateSerializer(
        data=request.data, context={'request': request, 'event': event}
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(status=status.HTTP_201_CREATED)


def process_rate_notifications_for_recent_events():
    """
    Find all games and tourneys ended an hour ago and send rate notifications.
    """
    hour_ago = timezone.now() - timedelta(hours=1)
    send_rate_notification_for_events(Game, hour_ago)
    send_rate_notification_for_events(Tourney, hour_ago)


def send_rate_notification_for_events(
    event_type: type[Game | Tourney], hour_ago: datetime
) -> bool:
    """
    Sends notification to all players in the event to rate other players.
    """
    events = event_type.objects.filter(
        end_time__gte=hour_ago, end_time__lt=timezone.now()
    )
    if issubclass(event_type, Game):
        notification_type = NotificationTypes.GAME_RATE
    else:
        notification_type = NotificationTypes.TOURNEY_RATE

    for event in events:
        send_event_notification_task.delay(event.id, notification_type)
        event.is_active = False
        event.save()
    return True
