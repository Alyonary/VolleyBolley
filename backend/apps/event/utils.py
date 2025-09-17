from datetime import datetime, timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response

from apps.event.models import Game, Tourney
from apps.players.serializers import (
    PlayerRateSerializer,
    PlayerShortSerializer,
)


def procces_rate_players_request(self, request, *args, **kwargs) -> Response:
    """
    Handles player rating in an event (Game or Tourney).

    GET: Returns a list of players available for rating.
    POST: Accepts ratings for players and saves them.
    """
    rater_player = request.user.player
    event = self.get_object()
    if self.request.method == 'GET':
        valid_players = PlayerRateSerializer.get_players_to_rate(
            rater_player, event
        )
        serializer = PlayerShortSerializer(valid_players, many=True)
        return Response({"players": serializer.data})

    serializer = PlayerRateSerializer(
        data=request.data,
        context={'request': request}
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(status=status.HTTP_200_OK)


def procces_rate_notifications_for_recent_events():
    """
    Find all games and tourneys ended an hour ago and send rate notifications.
    """

    hour_ago = timezone.now() - timedelta(hours=1)
    send_rate_notification_for_events(Game, hour_ago)
    send_rate_notification_for_events(Tourney, hour_ago)


def send_rate_notification_for_events(
    event_type: Game | Tourney,
    hour_ago: datetime
    ) -> bool:
    """
    Sends notification to all players in the event to rate other players.

    Implement notification logic after merging push service
    """
    ###доработаю после мержа пуш сервиса
    events = event_type.objects.filter(
        end_time__gte=hour_ago,
        end_time__lt=timezone.now()
    )
    for event in events:
        # send_rate_notification(event)
        event.is_active = False
        event.save()
    return True