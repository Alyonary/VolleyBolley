import logging
from typing import Any

from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import exceptions, serializers

from apps.api.enums import APIEnums
from apps.players.constants import PlayerStrEnums
from apps.players.serializers import PlayerAuthSerializer

logger = logging.getLogger(__name__)


class LoginSerializer(serializers.Serializer):
    """Serialize data after successful authentication of player."""

    player = PlayerAuthSerializer(
        read_only=True,
        help_text='Player data')
    access_token = serializers.CharField(
        max_length=APIEnums.TOKEN_MAX_LENGTH,
        read_only=True,
        help_text="JWT access token",
        example="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    )
    refresh_token = serializers.CharField(
        max_length=APIEnums.TOKEN_MAX_LENGTH,
        read_only=True,
        help_text="JWT refresh token",
        example="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    )


class AuthBaseSerializer(serializers.Serializer):
    """Generic authentication serializer."""

    given_name = serializers.CharField(required=False, allow_blank=True)
    family_name = serializers.CharField(required=False, allow_blank=True)
    name = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    phone_number = PhoneNumberField(required=False, allow_blank=True)
    phone = PhoneNumberField(required=False, allow_blank=True)

    def extract_name_last_name(
        self, validated_data: dict[str, Any]
    ) -> tuple[str, str]:
        """Extract users first and last names from id_token.

        Returns:
            The tuple (first_name, last_name).
        """
        first_name: str | None = validated_data.get('given_name')
        last_name: str | None = validated_data.get('family_name')
        full_name: str | None = validated_data.get('name')
        email: str | None = validated_data.get('email')

        if first_name and last_name:
            return first_name, last_name

        if full_name:
            if len(full_name) > 1:
                return full_name.split()[0], ' '.join(full_name.split()[1:])

            return full_name, full_name

        if email:
            return self.configure_from_email(email)

        return (
            PlayerStrEnums.DEFAULT_FIRST_NAME.value,
            PlayerStrEnums.DEFAULT_LAST_NAME.value
        )

    def configure_from_email(self, email: str) -> tuple[str, str]:
        """Configure first_name, last_name from users email.

        Returns:
            The tuple (first_name, last_name).
        """
        full_name = email.split('@')[0]

        if '.' in full_name:
            return full_name.rsplit('.', 1)

        if '_' in full_name:
            return full_name.rsplit('_', 1)

        return full_name, full_name

    def get_user_data(self, validated_data: dict[str, Any]) -> dict[str, Any]:
        """Configure user data from 'id_token'."""
        phone_number: str | None = validated_data.get('phone_number')
        first_name, last_name = self.extract_name_last_name(validated_data)
        email: str | None = validated_data.get('email')

        return {
            'phone_number': phone_number,
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
            'username': self.get_username(validated_data)
        }

    def get_username(self, validated_data: dict[str, Any]) -> str:
        """Appropriate method should be implemented.

        Rewrite this function in your authentication process.
        """
        raise NotImplementedError

    def create(self, validated_data: dict[str, Any]) -> dict[str, Any]:
        return self.get_user_data(validated_data)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        attrs['phone_number'] = attrs.get('phone_number') or attrs.get('phone')

        return attrs


class FirebaseBaseSerializer(AuthBaseSerializer):
    """Generic Firebase serializer."""

    user_id = serializers.CharField(required=True)
    phone = PhoneNumberField(
        required=False, allow_blank=True, source='firebase.identities.phone'
    )


class FirebasePhoneSerializer(FirebaseBaseSerializer):
    """Serialize Firebase user data for auth via phone number."""

    def validate(self, attrs):
        attrs = super().validate(attrs)

        if not attrs['phone_number']:
            raise exceptions.ValidationError(
                'Missing phone_number in id_token.'
            )

        return attrs

    def get_username(self, validated_data: dict[str, Any]) -> str:
        """Configure username from 'phone_number'."""
        return validated_data.get('phone_number')


class FirebaseFacebookSerializer(FirebaseBaseSerializer):
    """Serialize Firebase user data for auth via facebook."""

    email = serializers.EmailField(
        required=True, allow_blank=False, allow_null=False
    )

    def get_username(self, validated_data: dict[str, Any]) -> str:
        """Configure username from 'email'."""
        return validated_data.get('email')


class FirebaseGoogleSerializer(FirebaseFacebookSerializer):
    """Serialize Firebase user data for auth via google."""


class GoogleUserDataSerializer(AuthBaseSerializer):
    """Serialize user data for google authentication."""

    email = serializers.EmailField(
        required=True, allow_blank=False, allow_null=False
    )

    def get_username(self, validated_data: dict[str, Any]) -> str:
        """Configure username from 'email'."""
        return validated_data.get('email')
