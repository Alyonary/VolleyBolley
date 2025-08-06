from rest_framework import serializers

from apps.users.models import User
from .mixins import GameFieldMapMixin
from .models import Game


class GameCreateSerializer(GameFieldMapMixin):
    """Принимает JSON от фронта при POST /games."""
    players = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        many=True,
    )

    class Meta:
        model = Game
        fields = (
            'court', 'message', 'start_time', 'end_time',
            'gender', 'levels', 'is_private', 'maximum_players',
            'price_per_person', 'payment_type', 'payment_account',
            'players',
        )

    def validate(self, attrs):
        players = attrs.get('players', [])
        limit = attrs.get('max_players')
        if limit and len(players) > limit:
            raise serializers.ValidationError(
                'Количество игроков превышает лимит'
            )
        return attrs

    def create(self, validated_data):
        players = validated_data.pop('players', [])
        game = super().create(
            {**validated_data, 'host': self.context['request'].user}
        )
        game.players.set(players)
        return game


class GameResponseSerializer(GameFieldMapMixin):
    """Отдаёт детальное представление игры после успешного создания
    и при GET /games/{id}.
    """

    game_id = serializers.IntegerField(source='id', read_only=True)
    court_id = serializers.IntegerField(source='court.id', read_only=True)
    players = serializers.SerializerMethodField()

    class Meta(GameFieldMapMixin.Meta):
        model = Game
        fields = (
            'game_id', 'court_id', 'message', 'start_time', 'end_time',
            'gender', 'levels', 'is_private', 'maximum_players',
            'price_per_person', 'currency_type', 'payment_type',
            'payment_account', 'players',
        )

    def get_players(self, obj):
        return [{'player_id': u.id} for u in obj.players.all()]
