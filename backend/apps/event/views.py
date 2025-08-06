from rest_framework.viewsets import ModelViewSet

from .models import Game
from .permissions import IsHostOrReadOnly
from .serializers import GameSerializer, GameDetailSerializer


class GameViewSet(ModelViewSet):
    queryset = Game.objects.all()
    permission_classes = (IsHostOrReadOnly,)

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return GameDetailSerializer
        else:
            return GameSerializer

    def perform_create(self, serializer):
        game = serializer.save(
            host=self.request.user)
        game.players.add(self.request.user)
