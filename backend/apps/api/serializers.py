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
