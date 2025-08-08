import logging

from django.contrib.auth import get_user_model
from google.auth.transport import requests
from google.oauth2 import id_token
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from social_django.utils import load_backend, load_strategy

from apps.api.serializers import LoginSerializer
from apps.players.constants import BASE_PAYMENT_DATA
from apps.players.models import Player
from apps.players.pipeline import _get_or_create_player
from volleybolley.settings import SOCIAL_AUTH_GOOGLE_OAUTH2_KEY

logger = logging.getLogger(__name__)

User = get_user_model()

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
    """Authenticate user via google.
    
    Client can use either access_token or token_id received from
    google to be authenticated in the app.
    """
    def post(self, request):
        if 'access_token' in request.data:
            user = self._auth_via_access_token(request.data['access_token'])
        
        elif 'id_token' in request.data:
            user = self._auth_via_id_token(request.data['id_token'])
        
        else:
            return Response(
                {"error": "Need access_token or id_token"},
                status=status.HTTP_400_BAD_REQUEST
            )

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

    def _auth_via_access_token(self, token):
        """Authenticate via 'access_token'."""
        strategy = load_strategy(self.request)
        backend = load_backend(strategy, 'google-oauth2', None)
        return backend.do_auth(token)

    def _auth_via_id_token(self, token):
        """Authenticate via 'id_token'."""
        
        try:
            user_data_verified = id_token.verify_oauth2_token(
                token,
                requests.Request(),
                SOCIAL_AUTH_GOOGLE_OAUTH2_KEY
            )
            user_data_cleaned = self._get_user_data(user_data_verified)
            user = User.objects.filter(
                email=user_data_cleaned['email']
            ).first()
            if user is None:
                user = User.objects.create(**user_data_cleaned)
            _get_or_create_player(user, BASE_PAYMENT_DATA)
            return user
        except ValueError as e:
            return Response(
            {'error': e},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def _get_user_data(self, user_data_verified):
        email = user_data_verified.get('email', None)
        first_name = user_data_verified.get('given_name', None)
        last_name = user_data_verified.get('family_name', None)
        name = user_data_verified.get('name', None)
        if email is None:
            raise ValueError('id_token has no user email')
        if first_name is None and name is not None:
            first_name = name if ' ' not in name else name.split(' ', 1)[0]
            if name is None:
                first_name = email.split('@', 1)[0]
        if last_name is None and name is not None:
            last_name = name if ' ' not in name else name.split(' ', 1)[1]
            if name is None:
                last_name = first_name
        return {
            'email': email,
            'first_name': first_name,
            'last_name': last_name
        }
