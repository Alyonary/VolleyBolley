from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets

from .filters import PlayerLevelCountryFilter
from .serializers import PlayerSerializer

User = get_user_model()


class PlayerViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Представление (ViewSet) для получения списка игроков.


    Это 'ReadOnlyModelViewSet', который предоставляет только
    операции чтения (GET).

    Он позволяет получать список пользователей и фильтровать их по
    уровню навыков (`level`) и стране (`country`).
    """

    queryset = User.objects.all()
    serializer_class = PlayerSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('level', 'country')
    filterset_class = PlayerLevelCountryFilter
