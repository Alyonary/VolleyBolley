import logging

import firebase_admin
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from firebase_admin import auth, credentials
from rest_framework_simplejwt.tokens import RefreshToken

from apps.api.serializers import LoginSerializer
from apps.players.models import Player

logger = logging.getLogger(__name__)


def get_serialized_data(user=None) -> LoginSerializer | None:
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

    return None


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
            logger.error(f"Firebase initialization failed: {e}")
            raise ImproperlyConfigured(
                "Firebase is not properly configured"
            ) from e
    
    def verify_id_token(self, id_token):
        """Verify Firebase ID token."""
        try:
            decoded_token = auth.verify_id_token(id_token)
            return decoded_token
        except auth.ExpiredIdTokenError:
            logger.warning("Firebase ID token has expired")
            return None
        except auth.InvalidIdTokenError:
            logger.warning("Invalid Firebase ID token")
            return None
        except Exception as e:
            logger.error(f"Firebase token verification failed: {e}")
            return None


firebase_auth = FirebaseAuth()
