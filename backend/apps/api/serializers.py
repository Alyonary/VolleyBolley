from rest_framework import serializers

from apps.players.serializers import PlayerAuthSerializer


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
    """Serialize user data."""
    email = serializers.EmailField()
    given_name = serializers.CharField(required=False)
    family_name = serializers.CharField(required=False)
    name = serializers.CharField(required=False)

    def validate_email(self, value):
        if not value:
            raise serializers.ValidationError('id_token has no user email')
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
