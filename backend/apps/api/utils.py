import logging

import firebase_admin
from django.conf import settings

# from django.core.exceptions import ImproperlyConfigured
from firebase_admin import auth, credentials
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from apps.api.serializers import LoginSerializer
from apps.players.models import Player
from apps.users.models import User

logger = logging.getLogger(__name__)


def get_serialized_data(user: User) -> LoginSerializer:
    """Get serialized data for response.
    
    Returns a JSON response containing access_token, refresh_token,
    and player instance.
    """
    if user and user.is_active:
        refresh = RefreshToken.for_user(user)
        serializer = LoginSerializer(
            instance={
                'access_token': str(refresh.access_token),
                'refresh_token': str(refresh),
                'player': Player.objects.get(user=user)
            }
        )
        logger.info('Response data are successfully generated.')

        return serializer

    raise ValidationError('Cannot serialize data for empty or inactive user.')


def get_or_create_user(
    user: User | None, user_data_cleaned: dict[str, str]
) -> User:
    """Get user from DB or create a new one."""
    if user is None:
        user = User.objects.create(**user_data_cleaned)
        logger.info(f'New user id={user.id} has been created.')

    else:
        logger.info(f'Got user id={user.id} from database.')

    player, created = Player.objects.get_or_create(user=user)

    if created:
        logger.info(
            f'Default player id={player.id} is created '
            f'for user id={user.id}.'
        )
    else:
        logger.info(f'Got player id={player.id} from database.')

    return user


def return_auth_response_or_raise_exception(user: User) -> Response:
    """Return response with status code 200 or raise Exception."""
    serializer = get_serialized_data(user)
    logger.info(
        f'User id={user.id} has been successful authenticated.'
    )

    return Response(serializer.data, status=status.HTTP_200_OK)


class FirebaseAuth:
    """Firebase authentication utility class."""

    def __init__(self):
        self._initialize_firebase()

    def _initialize_firebase(self):
        """Initialize Firebase app if not already initialized."""
        try:
            if not firebase_admin._apps:
                cred = credentials.Certificate(
                    settings.FIREBASE_SERVICE_ACCOUNT
                )
                firebase_admin.initialize_app(cred)

        except Exception as e:
            logger.error(f'Firebase initialization failed: {e}.')
            # Disabled for testing
            # raise ImproperlyConfigured(
            #    'Firebase is not properly configured.'
            # ) from e

    def verify_id_token(self, id_token):
        """Verify Firebase ID token."""
        try:
            decoded_token = auth.verify_id_token(id_token)
            if decoded_token and isinstance(decoded_token, dict):
                logger.info('Firebase token is successfully decoded.')

                return decoded_token

            raise ValidationError('Decoded Firebase ID token is empty.')

        except auth.ExpiredIdTokenError as e:
            raise ValidationError(
                f'Firebase ID token has expired: {e}.'
            ) from e

        except auth.InvalidIdTokenError as e:
            raise ValidationError(f'Invalid Firebase ID token: {e}.') from e

        except Exception as e:
            raise ValidationError(
                f'Firebase token verification failed: {e}.'
            ) from e


firebase_auth = FirebaseAuth()
