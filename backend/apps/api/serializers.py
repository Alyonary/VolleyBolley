import logging

from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers

from apps.players.constants import PlayerStrEnums
from apps.players.serializers import PlayerAuthSerializer

logger = logging.getLogger(__name__)

class LoginSerializer(serializers.Serializer):
    """Serialize data after successful authentication of player."""
    
    player = PlayerAuthSerializer(read_only=True)
    access_token = serializers.CharField(
        max_length=1000,
        read_only=True
    )
    refresh_token = serializers.CharField(
        max_length=1000,
        read_only=True
    )

class GoogleUserDataSerializer(serializers.Serializer):
    """Serialize user data for google authentication."""
    email = serializers.EmailField()
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

        first_name = (first_name
                      or (name.split()[0] if name
                          else email.split('@')[0]))
        last_name = (last_name
                     or (name.split()[1] if name and len(name.split()) > 1
                         else first_name))

        return {
            'email': email,
            'first_name': first_name,
            'last_name': last_name
        }


class FirebaseUserDataSerializer(serializers.Serializer):
    """Serialize Firebase user data."""
    
    user_id = serializers.CharField(required=True)
    phone_number = PhoneNumberField(required=True)
    
    def create(self, validated_data):
        """Extract user data from Firebase response."""
        phone_number = validated_data.get('phone_number')
        first_name = PlayerStrEnums.DEFAULT_FIRST_NAME.value
        last_name = PlayerStrEnums.DEFAULT_LAST_NAME.value

        return {
            'phone_number': phone_number,
            'first_name': first_name,
            'last_name': last_name,
        }
