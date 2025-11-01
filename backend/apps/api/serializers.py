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

    player = PlayerAuthSerializer(read_only=True)
    access_token = serializers.CharField(
        max_length=APIEnums.TOKEN_MAX_LENGTH, read_only=True
    )
    refresh_token = serializers.CharField(
        max_length=APIEnums.TOKEN_MAX_LENGTH, read_only=True
    )


class GoogleUserDataSerializer(serializers.Serializer):
    """Serialize user data for google authentication."""

    email = serializers.EmailField(required=True)
    given_name = serializers.CharField(required=False)
    family_name = serializers.CharField(required=False)
    name = serializers.CharField(required=False)

    def validate_email(self, value):
        if not value:
            error_msg = 'id_token has no user email'
            logger.error(error_msg)
            raise serializers.ValidationError(error_msg)
        return value

    def create(self, validated_data):
        email = validated_data['email']
        first_name = validated_data.get('given_name')
        last_name = validated_data.get('family_name')
        name = validated_data.get('name')

        first_name = first_name or (
            name.split()[0] if name else email.split('@')[0]
        )
        last_name = last_name or (
            name.split()[1] if name and len(name.split()) > 1 else first_name
        )

        return {
            'email': email,
            'username': email,
            'first_name': first_name,
            'last_name': last_name,
        }


class FirebaseBaseSerializer(serializers.Serializer):
    """Generic Firebase serializer."""

    user_id = serializers.CharField(required=True)
    given_name = serializers.CharField(required=False, allow_blank=True)
    family_name = serializers.CharField(required=False, allow_blank=True)
    name = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    phone_number = PhoneNumberField(required=False, allow_blank=True)
    phone = PhoneNumberField(
        required=False, allow_blank=True, source='firebase.identities.phone'
    )

    def extract_name_last_name(
        self, validated_data: dict[str, Any]
    ) -> tuple[str, str]:
        """Extract users first and last names from Firebase id_token.

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
            PlayerStrEnums.DEFAULT_LAST_NAME.value,
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


class FirebasePhoneSerializer(FirebaseBaseSerializer):
    """Serialize Firebase user data for auth via phone number."""

    def validate(self, attrs):
        attrs = super().validate(attrs)
        attrs['phone_number'] = attrs.get('phone_number') or attrs.get('phone')

        if not attrs['phone_number']:
            raise exceptions.ValidationError(
                'Missing phone_number in Firebase id_token.'
            )

        return attrs

    def create(self, validated_data):
        """Extract user data from Firebase response."""
        phone_number = validated_data.get('phone_number')
        first_name, last_name = self.extract_name_last_name(validated_data)
        email = validated_data.get('email')
        return {
            'phone_number': phone_number,
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
            'username': phone_number,
        }


class FirebaseFacebookSerializer(FirebaseBaseSerializer):
    """Serialize Firebase user data for auth via facebook."""

    email = serializers.EmailField(required=True)

    def create(self, validated_data):
        """Extract user data from Firebase response."""
        phone_number = validated_data.get(
            'phone_number'
        ) or validated_data.get('phone')
        first_name, last_name = self.extract_name_last_name(validated_data)
        email = validated_data.get('email')

        return {
            'phone_number': phone_number,
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
            'username': email,
        }


class FirebaseGoogleSerializer(FirebaseFacebookSerializer):
    """Serialize Firebase user data for auth via google."""
