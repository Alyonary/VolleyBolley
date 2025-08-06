from datetime import datetime

from django.contrib.auth import get_user_model
from djoser.serializers import UserSerializer
from rest_framework import serializers

from apps.core.models import (
    CurrencyType,
    GameInvitation,
    GameLevel,
    Gender,
    Payment,
)
from apps.courts.models import Court
from apps.courts.serializers import LocationSerializer
from apps.event.models import Game

User = get_user_model()


class BaseGameSerializer(serializers.ModelSerializer):

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

    currency_type = serializers.CharField(
        required=False
    )

    payment_account = serializers.CharField(
        required=False
    )

    maximum_players = serializers.IntegerField(
        source='max_players'
    )

    class Meta:
        model = Game
        fields = [
            'game_id',
            'host',
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
        ]

    def validate(self, value):
        request = self.context.get('request', None)
        payment = Payment.objects.get(
            owner=request.user,
            payment_type=value.get('payment_type')
        )
        if not payment or payment.payment_account is None:
            raise serializers.ValidationError(
                'No payment account found for this payment type')
        value['payment_account'] = payment.payment_account

        '''
        Пока пользователи не настроены, отдаем так.
        Должно быть что-то вроде:
        player = request.user.player
        currency_types = CurrencyType.objects.filter(
                            country=player.location.country)
        '''
        currency_type = CurrencyType.objects.first()
        value['currency_type'] = currency_type
        return value


class GameSerializer(BaseGameSerializer):

    players = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        many=True
    )
    court_id = serializers.PrimaryKeyRelatedField(
        source='court',
        queryset=Court.objects.all()
    )

    class Meta(BaseGameSerializer.Meta):
        model = BaseGameSerializer.Meta.model
        fields = BaseGameSerializer.Meta.fields + [
            'court_id',
            'players'
        ]

    def create(self, validated_data):
        print(validated_data)
        players = validated_data.pop('players')
        levels = validated_data.pop('player_levels')
        game = Game.objects.create(**validated_data)
        game.player_levels.set(levels)
        self.create_invitations(game=game, sender=game.host, players=players)
        return game

    def validate_players(self, value):
        host = self.context['request'].user
        if host in value:
            raise serializers.ValidationError(
                'Нельзя отправить приглашение на игру себе.')
        if len(value) != len(set(value)):
            raise serializers.ValidationError(
                'Игроки не должны повторяться')
        return value

    @staticmethod
    def create_invitations(game, sender=None, players=None):
        '''Создает приглашения на игру.

        Принимает на вход объект игры, список игроков для создания приглашений
        и отправителя. Если отправитель является организатором игры,
        то отправителя можно не указывать.
        '''

        bulk_list = []
        if not sender:
            sender = game.host
        for player in players:
            if GameInvitation.objects.filter(
                    host=sender, invited=player, game=game).exists():
                raise serializers.ValidationError(
                    f'Приглашение на игру {game} игроку'
                    f'{player} от {sender} уже существует!'
                )
            invitation = GameInvitation(
                host=sender, invited=player, game=game)
            bulk_list.append(invitation)
        GameInvitation.objects.bulk_create(bulk_list)


class GameDetailSerializer(BaseGameSerializer):

    host = UserSerializer()

    game_type = serializers.SerializerMethodField(read_only=True)

    court_location = LocationSerializer(source='court.location')

    players = UserSerializer(many=True)

    class Meta(BaseGameSerializer.Meta):
        model = BaseGameSerializer.Meta.model
        fields = BaseGameSerializer.Meta.fields + [
            'game_type',
            'court_location',
            'players'
        ]

    def get_game_type(self, obj):
        """Хардкод фу-фу-фу.
        Возвращаемые значения:
        MY, UPCOMING, ARCHIVE, INVITES, ACTIVE
        """
        request = self.context.get('request', None)
        if obj.host == request.user:
            return 'MY'
        elif GameInvitation.objects.filter(
                invited=request.user, game=obj).exists():
            return 'INVITE'
        elif obj.end_time < datetime.now().strftime('%Y-%m-%d %H:%M'):
            return 'ARCHIVE'
        elif obj.start_time > datetime.now().strftime('%Y-%m-%d %H:%M'):
            return 'UPCOMING'
        else:
            return 'ACTIVE'


class TourneySerializer(serializers.ModelSerializer):
    pass
