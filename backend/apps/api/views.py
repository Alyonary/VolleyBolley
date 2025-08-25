import logging

from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from google.auth.transport import requests
from google.oauth2 import id_token
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from social_django.utils import load_backend, load_strategy

from apps.api.serializers import GoogleUserDataSerializer
from apps.api.utils import get_serialized_data
from apps.players.models import Player
from volleybolley.settings import SOCIAL_AUTH_GOOGLE_OAUTH2_KEY

logger = logging.getLogger(__name__)

User = get_user_model()


class LogoutView(APIView):
    """Logout view class."""

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['refresh'],
            properties={
                'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='Refresh token to blacklist'),
            },
        ),
        responses={205: 'Reset Content', 400: 'Bad Request'},
        operation_summary="Logout by blacklisting refresh token",
        tags=['auth'],
    )
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
    
    Redirect client to base social-auth url ('api:social:begin')
    if there is no data in request or request method is 'GET'.
    """
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'access_token': openapi.Schema(type=openapi.TYPE_STRING, description='Google access token'),
                'id_token': openapi.Schema(type=openapi.TYPE_STRING, description='Google ID token'),
            },
            anyOf=[
                {'required': ['access_token']},
                {'required': ['id_token']}
            ],
        ),
        responses={
            200: openapi.Response('Successful authentication', GoogleUserDataSerializer),
            401: 'Authentication failed',
        },
        operation_summary="Authenticate user via Google (access_token or id_token)",
        tags=['auth'],
    )
    def post(self, request):
        if 'access_token' in request.data:
            user = self._auth_via_access_token(request.data['access_token'])
        
        elif 'id_token' in request.data:
            user = self._auth_via_id_token(request.data['id_token'])

        else:
            return redirect('api:social:begin', backend='google-oauth2')

        if user and user.is_active:
            serializer = get_serialized_data(user)

            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(
            {'error': 'Authentication failed'},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    @swagger_auto_schema(
        operation_summary="Redirect to Google OAuth2 social auth",
        responses={302: 'Redirect'},
        tags=['auth'],
    )
    def get(self, request):
        return redirect('api:social:begin', backend='google-oauth2')

    def _auth_via_access_token(self, token):
        """Authenticate via 'access_token'."""
        strategy = load_strategy(self.request)
        backend = load_backend(strategy, 'google-oauth2', None)
        strategy.session_set('via_access_token', True)
        strategy.request.via_access_token = True

        return backend.do_auth(token)

    def _auth_via_id_token(self, token):
        """Authenticate via 'id_token'."""
        
        try:
            user_data_verified = id_token.verify_oauth2_token(
                token,
                requests.Request(),
                SOCIAL_AUTH_GOOGLE_OAUTH2_KEY
            )
            serializer = GoogleUserDataSerializer(data=user_data_verified)
            serializer.is_valid(raise_exception=True)
            user_data_cleaned = serializer.save()
            user = User.objects.filter(
                email=user_data_cleaned['email']
            ).first()
            if user is None:
                user = User.objects.create(**user_data_cleaned)
            Player.objects.get_or_create(user=user)

            return user

        except ValueError as e:
            return Response(
            {'error': e},
            status=status.HTTP_400_BAD_REQUEST,
        )
