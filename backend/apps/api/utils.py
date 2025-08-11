from rest_framework_simplejwt.tokens import RefreshToken

from apps.api.serializers import LoginSerializer
from apps.players.models import Player


def get_serialized_data(user=None) -> LoginSerializer:
    if user and user.is_active:
       refresh = RefreshToken.for_user(user)
       serializer = LoginSerializer(
           {
               'access_token': str(refresh.access_token),
               'refresh_token': str(refresh),
               'player': Player.objects.get(user=user)
           }
       )
       return serializer
