from datetime import datetime

from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
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
    '''Game serializer uses for create, list requests.'''

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
        players = validated_data.pop('players')
        levels = validated_data.pop('player_levels')
        game = Game.objects.create(**validated_data)
        game.player_levels.set(levels)
        for player in players:
            serializer = GameInviteSerializer(
                    data={
                        'host': game.host.id,
                        'invited': player.id,
                        'game': game.id
                    },
                    context=self.context
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
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


class GameDetailSerializer(BaseGameSerializer):
    '''Game serializer uses for retrieve requests.'''

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
        '''Assigns a type to the game.
        Returning values:
        MY, UPCOMING, ARCHIVE, INVITES, ACTIVE
        '''
        request = self.context.get('request', None)
        if obj.host == request.user:
            return 'MY'
        elif GameInvitation.objects.filter(
                invited=request.user, game=obj).exists():
            return 'INVITES'
        elif obj.end_time < datetime.now().strftime('%Y-%m-%d %H:%M'):
            return 'ARCHIVE'
        elif obj.start_time > datetime.now().strftime('%Y-%m-%d %H:%M'):
            return 'UPCOMING'
        else:
            return 'ACTIVE'


class GameInviteSerializer(serializers.ModelSerializer):

    invited = serializers.PrimaryKeyRelatedField(
        write_only=True, queryset=User.objects.all())

    class Meta:
        model = GameInvitation
        fields = ('host', 'invited', 'game')
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=GameInvitation.objects.all(),
                fields=('host', 'invited', 'game'),
                message=_('Такое приглашение уже существует!'),
            )
        ]

    def validate(self, attrs):
        host = attrs.get('host')
        invited = attrs.get('invited')
        if host == invited:
            raise serializers.ValidationError(
                'Нельзя отправить приглашение на игру себе.')
        return attrs


class TourneySerializer(serializers.ModelSerializer):
    pass


class ShortGameSerializer(serializers.ModelSerializer):

    class Meta:
        model = Game
        '''
        "game_id": 0,
        "host": {
            "player_id": 0,
            "first_name": "Test",
            "last_name": "Test",
            "avatar": "url",
            "level": "PRO"
        },
        "court_location": {
            "longitude": 0.1,
            "latitude": 0.1,
            "court_name": "Karon",
            "location_name": "Russia, Moscow"
        },
        "message": "Hey there!",
        "start_time": "2025-07-01 14:30",
        "end_time": "2025-07-01 14:30"
    }
    '''

    def to_representation(self, instance):
        '''Переопределить для выдачи с главным ключом "games".'''
        return super().to_representation(instance)
