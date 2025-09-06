# from django.db.models import Q
# from django.utils.timezone import now
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.players.serializers import (
    PlayerRateSerializer,
    PlayerShortSerializer,
)

# from apps.event.models import Game, GameInvitation
# from apps.event.permissions import IsHostOrReadOnly
# from apps.event.serializers import (
#     GameDetailSerializer,
#     GameInviteSerializer,
#     GameSerializer,
#     GameShortSerializer,
# )


class GameViewSet(ModelViewSet):
    """Provides CRUD operations for the Game model."""
    permission_classes = (IsAuthenticated,)
    
    @action(
        methods=['post', 'get'],
        detail=True,
        url_path='rate-players',
    )
    def rate_players(self, request, pk):
        return self.procces_rate_player_request(self, request, pk)

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
        elif self.request.method == 'POST':
            serializer = PlayerRateSerializer(
                data=request.data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
        return Response(
            status=status.HTTP_200_OK,
            data=valid_players.validated_data
        )