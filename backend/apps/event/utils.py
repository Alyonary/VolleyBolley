from rest_framework import status
from rest_framework.response import Response

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
            {'players': serializer.data}, status=status.HTTP_200_OK
        )

    serializer = PlayerRateSerializer(
        data=request.data, context={'request': request, 'event': event}
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(status=status.HTTP_201_CREATED)
