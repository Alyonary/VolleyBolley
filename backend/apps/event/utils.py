from datetime import datetime

from backend.apps.event.models import Game, Tourney
from backend.apps.players.models import PlayerEventRate
from django.contrib.contenttypes.models import ContentType
from rest_framework import status
from rest_framework.response import Response

from apps.players.serializers import (
    PlayerRateSerializer,
    PlayerShortSerializer,
)


def procces_rate_players_request(self, request, pk) -> Response:
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


def procces_skip_players_rate_request(self, request, pk) -> Response:
    """
    Increments skip counter for a player-event pair.

    If skip < 3, player can still be reminded to rate.
    """
    rater_player = request.user.player
    event = self.get_object()
    event_ct = ContentType.objects.get_for_model(type(event))
    game_rate = PlayerEventRate.objects.filter(
        player=rater_player,
        content_type=event_ct,
        object_id=event.id,
        defaults={'skip': 1}
    ).first()
    game_rate.skip += 1
    game_rate.save()
    return Response(status=status.HTTP_200_OK)


def create_event_rate_objects_and_notify(
    event_model: Game | Tourney,
    hour_ago: datetime
) -> None:
    """
    Bulk create PlayerEventRate objects for all players in an event.

    After creation for all players, the event becomes inactive.
    """
    past_events = event_model.objects.filter(
        end_time__gte=hour_ago,
        is_active=True
    )
    event_ct = ContentType.objects.get_for_model(event_model)
    for event in past_events:
        player_rates = []
        for player in event.players.all():
            player_rates.append(
                PlayerEventRate(
                    player=player,
                    content_type=event_ct,
                    object_id=event.id,
                )
            )
        PlayerEventRate.objects.bulk_create(
            player_rates,
            ignore_conflicts=True
        )
        event.is_active = False
        event.save()
        send_rate_notification(event)


def send_rate_notification(event: Game | Tourney) -> None:
    """
    Sends notification to all players in the event to rate other players.

    Implement notification logic after merging push service
    """
    # Реализовать отправку уведомлений после мержа пуш сервиса
    pass