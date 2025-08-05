from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.core.models import CurrencyType, GameLevel, Gender
from apps.courts.models import Court

from .models import Game

User = get_user_model()


class GameSerializer(serializers.ModelSerializer):

    game_id = serializers.IntegerField(source='pk', read_only=True)

    host = serializers.HiddenField(
        write_only=True,
        default=serializers.CurrentUserDefault()
    )
    start_time = serializers.DateTimeField(format='%Y-%m-%d %H:%M')

    end_time = serializers.DateTimeField(format='%Y-%m-%d %H:%M')

    levels = serializers.SlugRelatedField(
        slug_field='name',
        queryset=GameLevel.objects.all(),
        source='player_levels',
        many=True
    )

    gender = serializers.SlugRelatedField(
        slug_field='name',
        queryset=Gender.objects.all()
    )

    currency_type = serializers.SlugRelatedField(
        slug_field='currency_type',
        queryset=CurrencyType.objects.all()
    )

    maximum_players = serializers.IntegerField(
        source='max_players'
    )

    player_id = serializers.PrimaryKeyRelatedField(
        source='players',
        queryset=User.objects.all(),
        many=True
    )
    court_id = serializers.PrimaryKeyRelatedField(
        source='court',
        queryset=Court.objects.all()
    )

    class Meta:
        model = Game
        fields = [
            'game_id',
            'court_id',
            'message',
            'start_time',
            'end_time',
            'gender',
            'levels',
            'is_private',
            'maximum_players',
            'price_per_person',
            'currency_type',
            'payment_type',
            'payment_account',
            'player_id',
            'host'
        ]


class TourneySerializer(serializers.ModelSerializer):
    pass
