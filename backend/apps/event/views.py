# from django_filters import rest_framework as filters
from rest_framework.viewsets import ModelViewSet

from .models import Game
from .permissions import IsHostOrReadOnly
from .serializers import GameSerializer


class GameViewSet(ModelViewSet):
    queryset = Game.objects.all()
    serializer_class = GameSerializer
    permission_classes = (IsHostOrReadOnly,)

    def perform_create(self, serializer):
        serializer.save(
            host=self.request.user)
