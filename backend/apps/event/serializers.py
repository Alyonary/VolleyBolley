from rest_framework import serializers

from .models import Game


class GameSerializer(serializers.ModelSerializer):

    class Meta:
        model = Game
        exclude = ('is_active',)


class TourneySerializer(serializers.ModelSerializer):
    pass
