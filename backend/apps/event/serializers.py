from rest_framework import serializers

from apps.users.models import User
from .models import Game


class GameCreateSerializer(serializers.ModelSerializer):
    players = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        many=True,
    )

    class Meta:
        model = Game
        fields = (
            'title',
            'message',
            'date',
            'start_time',
            'end_time',
            'court',
            'gender',
            'player_levels',
            'max_players',
            'price_per_person',
            'payment_type',
            'payment_value',
            'tag_list',
            'is_private',
            'players',
        )

        def validate(self, attrs):
            players = attrs.get('players', [])
            max_players = attrs.get('max_players')
            if max_players and len(players) > max_players:
                raise serializers.ValidationError(
                    'Количество игроков превышает лимит'
                )
            return attrs

    def create(self, validated_data):
        players_data = validated_data.pop('players', [])
        game = Game.objects.create(
            **validated_data,
            host=self.context['request'].user,
        )
        game.players.set(players_data)
        return game


class GameDetailSerializer(serializers.ModelSerializer):
    players = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    host = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Game
        fields = ('id', 'title', 'players', 'host')
