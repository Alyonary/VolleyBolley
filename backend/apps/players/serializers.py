from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.users.models import Location

User = get_user_model()


class LocationSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Локации."""

    class Meta:
        model = Location
        fields = ('country', 'city')


class PlayerSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Пользователя."""

    location = LocationSerializer()

    class Meta:
        model = User
        fields = ('id', 'username', 'game_skill_level', 'location', 'rating')
