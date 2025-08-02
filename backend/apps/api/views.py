from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from social_django.utils import load_backend, load_strategy

from apps.api.serializers import LoginSerializer
from apps.players.models import Player


class LogoutView(APIView):
    """Представление для выхода из профиля."""
    def post(self, request) -> Response:
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class GoogleLogin(APIView):
    permission_classes = []

    def post(self, request):
        strategy = load_strategy(request)
        backend = load_backend(strategy, 'google-oauth2', None)
        
        try:
            user = backend.do_auth(request.data.get('id_token'))
            if user and user.is_active:
                refresh = RefreshToken.for_user(user)
                serializer = LoginSerializer(
                    {
                        'access_token': str(refresh.access_token),
                        'refresh_token': str(refresh),
                        'player': Player.objects.get(user=user)
                    }
                )
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(
                {'error': 'Authentication failed'},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
