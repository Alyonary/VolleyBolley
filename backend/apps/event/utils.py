from rest_framework import status
from rest_framework.response import Response

from apps.players.serializers import (
    PlayerRateSerializer,
    PlayerShortSerializer,
)


# использовать в actions game/tourney
def procces_rate_player_request(self, request, pk) -> Response:
    """
    Process the request to rate players in an event (Game or Tourney).
    Handles both GET and POST methods.
        1. GET: Returns a list of players that the rater can rate.
        2. POST: Accepts ratings for players and saves them.
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
