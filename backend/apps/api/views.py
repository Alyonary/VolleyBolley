import logging

from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from google.auth.transport import requests
from google.oauth2 import id_token
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from social_core.exceptions import AuthForbidden
from social_django.utils import (
    load_backend,
    load_strategy,
)

from apps.api.serializers import (
    FirebaseFacebookSerializer,
    FirebaseGoogleSerializer,
    FirebasePhoneSerializer,
    GoogleUserDataSerializer,
)
from apps.api.utils import (
    firebase_auth,
    get_or_create_user,
    return_auth_response_or_raise_exception,
)
from volleybolley.settings import SOCIAL_AUTH_GOOGLE_OAUTH2_KEY

logger = logging.getLogger(__name__)

User = get_user_model()


class AuthIdTokenMixin():
    """Mix a special auth method to API views.

    Provide the method to authenticate a user via the firebase id_token.
    """

    def _post(self, request, serializer):
        """Auth user via firebase token.

        A serializer choice depends on the authentication type:
        via phone-number, facebook, etc.
        """
        if 'id_token' in request.data:
            try:
                return self.auth_via_id_token(
                    request.data['id_token'],
                    serializer=serializer,
                )

            except ValidationError as e:
                error_msg = f'validation error: {e}'
                logger.error(error_msg)

                return Response(
                    {'error': error_msg},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            except Exception as e:
                error_msg = f'unexpected error: {e}'
                logger.error(error_msg)

                return Response(
                    {'error': error_msg},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        else:
            return Response(
                {'error': 'firebase id_token was not provided.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def auth_via_id_token(self, id_token, serializer):
        """Authenticate using Firebase ID token from frontend."""

        serializer = serializer(
            data=firebase_auth.verify_id_token(id_token)
        )
        serializer.is_valid(raise_exception=True)
        user_data_cleaned = serializer.save()

        # try to find user in DB by phone_number or email
        user = User.objects.filter(
            phone_number=user_data_cleaned['phone_number']
        ).first() or User.objects.filter(
            email=user_data_cleaned['email']
        ).first()

        user = get_or_create_user(user, user_data_cleaned)

        return return_auth_response_or_raise_exception(user)


class LogoutView(APIView):
    """Logout view class."""

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['refresh'],
            properties={
                'refresh': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Refresh token to blacklist'),
            },
        ),
        responses={205: 'Reset Content', 400: 'Bad Request'},
        operation_summary='Logout by blacklisting refresh token',
        tags=['auth'],
    )
    def post(self, request) -> Response:
        try:
            refresh_token = request.data.get('refresh_token', None)
            if not refresh_token:
                raise ValidationError('No refresh token is provided.')

            token = RefreshToken(refresh_token)
            token.blacklist()
            logger.info('Successful logout.')

            return Response(status=status.HTTP_205_RESET_CONTENT)

        except (ValidationError, TokenError) as e:
            logger.error(f'Logout failure: {e}.')

            return Response(status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f'Logout failure: {e}.')

            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
                'access_token': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Google access token'
                    ),
                'id_token': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Google ID token'
                    ),
            },
            anyOf=[
                {'required': ['access_token']},
                {'required': ['id_token']}
            ],
        ),
        responses={
            200: openapi.Response(
                'Successful authentication',
                GoogleUserDataSerializer
                ),
            401: 'Authentication failed',
        },
        operation_summary="Authenticate via Google (access_token or id_token)",
        tags=['auth'],
    )
    def post(self, request):
        try:
            data = request.data
            if 'access_token' in data:
                if data['access_token']:
                    logger.info(
                        'Starting authentication via google access_token.'
                    )

                    return self._auth_via_access_token(
                        request.data['access_token']
                    )

                raise ValidationError('Empty token.')

            if 'id_token' in data:
                if data['id_token']:
                    logger.info(
                        'Starting authentication via google id_token.'
                    )

                    return self._auth_via_id_token(data['id_token'])

                raise ValidationError('Empty token.')

            logger.info(
                'Redirected to authenticate via google without token.'
            )

            return redirect('api:social:begin', backend='google-oauth2')

        except ValidationError as e:
            error_msg = f'validation error: {e}.'
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
            error_msg = f'Unexpected error: {e}.'
            logger.error(error_msg)

            return Response(
                {'error': error_msg},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @swagger_auto_schema(
        operation_summary="Redirect to Google OAuth2 social auth",
        responses={302: 'Redirect'},
        tags=['auth'],
    )
    def get(self, request):
        logger.info(
            'Starting authentication via google without token.'
        )

        return redirect('api:social:begin', backend='google-oauth2')

    def _auth_via_access_token(self, token):
        """Authenticate via 'access_token'."""
        strategy = load_strategy(self.request)
        backend = load_backend(strategy, 'google-oauth2', None)
        strategy.session_set('via_access_token', True)
        strategy.request.via_access_token = True
        user = backend.do_auth(token)

        return return_auth_response_or_raise_exception(user)

    def _auth_via_id_token(self, token):
        """Authenticate via 'id_token'."""

        user_data_verified = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            SOCIAL_AUTH_GOOGLE_OAUTH2_KEY
        )
        if not user_data_verified:
            raise ValidationError('Invalid or expired google id_token')

        serializer = GoogleUserDataSerializer(data=user_data_verified)
        serializer.is_valid(raise_exception=True)
        user_data_cleaned = serializer.save()
        user = User.objects.filter(
            email=user_data_cleaned['email']
        ).first()
        user = get_or_create_user(user, user_data_cleaned)

        return return_auth_response_or_raise_exception(user)


class PhoneNumberLogin(APIView, AuthIdTokenMixin):
    """Authenticate user via phone number.

    An id_token generated by the Firebase app should be provided
    to authenticate a user.
    """

    def post(self, request):

        return self._post(request, FirebasePhoneSerializer)


class FacebookLogin(APIView, AuthIdTokenMixin):
    """Authenticate user via Facebook.

    An id_token generated by the Firebase app should be provided
    to authenticate a user.
    """

    def post(self, request):

        return self._post(request, FirebaseFacebookSerializer)


class GoogleLoginV2(APIView, AuthIdTokenMixin):
    """Authenticate user via Google.

    An id_token generated by the Firebase app should be provided
    to authenticate a user.
    """

    def post(self, request):

        return self._post(request, FirebaseGoogleSerializer)
