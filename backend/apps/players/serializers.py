from rest_framework import serializers

from apps.players.models import User


class PlayerShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'avatar')
