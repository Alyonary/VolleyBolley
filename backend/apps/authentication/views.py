import logging
from typing import Any

from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from drf_yasg.utils import swagger_auto_schema
from google.auth.transport import requests
from google.oauth2 import id_token
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from social_core.exceptions import AuthForbidden
from social_django.utils import (
    load_backend,
    load_strategy,
)

from apps.authentication.serializers import (
    CustomTokenRefreshSerializer,
    CustomTokenVerifySerializer,
    FirebaseFacebookSerializer,
    FirebaseGoogleSerializer,
    FirebasePhoneSerializer,
    GoogleUserDataSerializer,
)

# Импорт swagger схем
from apps.authentication.swagger_schemas import (
    AUTH_FACEBOOK_POST_SCHEMA,
    AUTH_GOOGLE_GET_SCHEMA,
    AUTH_GOOGLE_POST_SCHEMA,
    AUTH_GOOGLE_V2_POST_SCHEMA,
    AUTH_LOGOUT_POST_SCHEMA,
    AUTH_PHONE_POST_SCHEMA,
    AUTH_TOKEN_REFRESH_POST_SCHEMA,
    AUTH_TOKEN_VERIFY_POST_SCHEMA,
)
from apps.authentication.utils import (
    firebase_auth,
    get_or_create_user,
    return_auth_response_or_raise_exception,
)
from volleybolley.settings import SOCIAL_AUTH_GOOGLE_OAUTH2_KEY

logger = logging.getLogger(__name__)

User = get_user_model()


class AuthIdTokenMixin:
    """Mix a special auth method to API views.

    Provide the method to authenticate a user via 'id_token'.
    """

    def verify_id_token(self, token: str) -> dict[str, Any]:
        """Appropriate method should be implemented.

        Rewrite this function in your authentication process.
        """
        raise NotImplementedError

    def get_verified_user_data(self, token: str) -> dict[str, Any]:
        """Return verified user data from 'id_token'."""
        return self.verify_id_token(token)

    def _post(self, request, serializer: Serializer) -> Response:
        """Auth user via 'id_token'.

        A serializer choice depends on the authentication type:
        via phone-number, facebook, google, etc.
        """
        try:
            token = request.data.get('id_token')
            if token:
                return self.auth_via_id_token(
                    token=token,
                    serializer=serializer,
                )

            error_msg = 'No or empty id_token in request body'
            logger.error(error_msg)

            raise ValidationError(error_msg)

        except ValidationError as e:
            error_msg = f'validation error: {e}'
            logger.error(error_msg)
            return Response(
                {'error': error_msg},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except (requests.exceptions.GoogleAuthError, AuthForbidden) as e:
            error_msg = f'Failed to verify google id_token: {e}.'
            logger.error(error_msg)

            return Response(
                {'error': error_msg},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            error_msg = f'unexpected error: {e}'
            logger.error(error_msg)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def auth_via_id_token(
        self, token: str, serializer: Serializer
    ) -> Response:
        """Authenticate using 'id_token' from frontend."""
        user_verified_data = self.get_verified_user_data(token)
        serializer = serializer(data=user_verified_data)
        serializer.is_valid(raise_exception=True)
        user_data_cleaned = serializer.save()
        username = user_data_cleaned.get('username')

        if username:
            user = User.objects.filter(username=username).first()

        else:
            user = None

        user = get_or_create_user(user, user_data_cleaned)

        return return_auth_response_or_raise_exception(user)


class LogoutView(APIView):
    """Logout view class."""

    @swagger_auto_schema(**AUTH_LOGOUT_POST_SCHEMA)
    def post(self, request: Request) -> Response:
        try:
            refresh_token = request.data.get('refresh_token', None)
            if not refresh_token:
                raise ValidationError('No refresh token is provided.')

            token = RefreshToken(refresh_token)
            token.blacklist()
            logger.info('Successful logout.')

            return Response(status=status.HTTP_205_RESET_CONTENT)

        except (ValidationError, TokenError) as e:
            error_msg = f'Logout failed: {e}.'
            logger.error(error_msg)

            return Response(
                {'error': error_msg}, status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            error_msg = f'Internal server error: {e}.'
            logger.error(error_msg)

            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GoogleLogin(APIView, AuthIdTokenMixin):
    """Authenticate user via google.

    Client can use token_id received from google
    to be authenticated in the app.
    """

    @swagger_auto_schema(**AUTH_GOOGLE_POST_SCHEMA)
    def post(self, request: Request) -> Response:
        data = request.data

        if 'id_token' in data:
            logger.info('Starting authentication via google id_token.')
            return self._post(request, GoogleUserDataSerializer)

        if 'access_token' in data:
            logger.info('Starting authentication via google access_token.')
            return self.auth_via_access_token(data.get('access_token'))

        error_msg = "No 'id_token' or 'access_token' in request body."
        logger.error(error_msg)
        return Response(
            {'error': error_msg}, status=status.HTTP_400_BAD_REQUEST
        )

    def verify_id_token(self, token: str) -> dict[str, Any]:
        return id_token.verify_oauth2_token(
            token, requests.Request(), SOCIAL_AUTH_GOOGLE_OAUTH2_KEY
        )

    @swagger_auto_schema(**AUTH_GOOGLE_GET_SCHEMA)
    def get(self, request: Request) -> Response:
        logger.info('Starting authentication via google without token.')
        return redirect('api:social:begin', backend='google-oauth2')

    def auth_via_access_token(self, token: str) -> Response:
        """Authenticate via 'access_token'."""
        try:
            if not token:
                error_msg = 'Empty access_token in request body.'
                logger.error(error_msg)

                raise ValidationError(error_msg)

            strategy = load_strategy(self.request)
            backend = load_backend(strategy, 'google-oauth2', None)
            strategy.session_set('via_access_token', True)
            strategy.request.via_access_token = True
            user = backend.do_auth(token)

            return return_auth_response_or_raise_exception(user)

        except ValidationError as e:
            error_msg = f'Validation error: {e}.'
            logger.error(error_msg)

            return Response(
                {'error': error_msg},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except (requests.exceptions.GoogleAuthError, AuthForbidden) as e:
            error_msg = f'Failed to verify google id_token: {e}.'
            logger.error(error_msg)

            return Response(
                {'error': error_msg},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            error_msg = f'Internal server error: {e}.'
            logger.error(error_msg)

            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FirebaseAuthMixin(AuthIdTokenMixin):
    """Mix a special auth method to API views.

    Provide the method to authenticate a user via firebase 'id_token'.
    """

    def verify_id_token(self, token: str) -> dict[str, Any]:
        """Verify and decode firebase 'id_token'."""
        return firebase_auth.verify_id_token(token)


class PhoneNumberLogin(APIView, FirebaseAuthMixin):
    """Authenticate user via phone number.

    An 'id_token' generated by the Firebase app should be provided
    to authenticate a user.
    """

    @swagger_auto_schema(**AUTH_PHONE_POST_SCHEMA)
    def post(self, request: Request) -> Response:
        """Authenticate via phone number (firebase id_token)."""
        return self._post(request, FirebasePhoneSerializer)


class FacebookLogin(APIView, FirebaseAuthMixin):
    """Authenticate user via Facebook.

    An id_token generated by the Firebase app should be provided
    to authenticate a user.
    """

    @swagger_auto_schema(**AUTH_FACEBOOK_POST_SCHEMA)
    def post(self, request: Request) -> Response:
        """Authenticate via Facebook (firebase id_token)."""
        return self._post(request, FirebaseFacebookSerializer)


class GoogleLoginV2(APIView, FirebaseAuthMixin):
    """Authenticate user via Google.

    An id_token generated by the Firebase app should be provided
    to authenticate a user.
    """

    @swagger_auto_schema(**AUTH_GOOGLE_V2_POST_SCHEMA)
    def post(self, request: Request) -> Response:
        """Authenticate via Google (firebase id_token)."""
        return self._post(request, FirebaseGoogleSerializer)


class CustomTokenRefreshView(APIView):
    """Refresh access_token."""

    permission_classes = []
    authentication_classes = []

    @swagger_auto_schema(**AUTH_TOKEN_REFRESH_POST_SCHEMA)
    def post(self, request):
        serializer = CustomTokenRefreshSerializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)

            return Response(
                serializer.validated_data, status=status.HTTP_200_OK
            )

        except ValidationError as e:
            error_msg = f'validation error: {e}'
            logger.error(error_msg)
            return Response(
                {'error': error_msg},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except TokenError as e:
            error_msg = f'Invalid or expired refresh token: {e}'
            logger.error(error_msg)
            return Response(
                {'error': error_msg},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            error_msg = f'unexpected error: {e}'
            logger.error(error_msg)
            return Response(
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class CustomTokenVerifyView(APIView):
    """Verify access_token."""

    permission_classes = []
    authentication_classes = []

    @swagger_auto_schema(**AUTH_TOKEN_VERIFY_POST_SCHEMA)
    def post(self, request):
        serializer = CustomTokenVerifySerializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
            return Response(
                serializer.validated_data, status=status.HTTP_200_OK
            )

        except ValidationError as e:
            error_msg = f'validation error: {e}'
            logger.error(error_msg)
            return Response(
                {'error': error_msg},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except TokenError as e:
            error_msg = f'Invalid or expired access token: {e}'
            logger.error(error_msg)
            return Response(
                {'error': error_msg},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            error_msg = f'unexpected error: {e}'
            logger.error(error_msg)
            return Response(
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
