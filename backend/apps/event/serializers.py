from datetime import datetime
from django.contrib.auth import get_user_model
from djoser.serializers import UserSerializer
from rest_framework import serializers

from apps.event.models import Game
from apps.core.models import (
    CurrencyType, GameLevel, Gender, Payment, GameInvitation
)
from apps.courts.models import Court
from apps.courts.serializers import LocationSerializer


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

    currency_type = serializers.SerializerMethodField(read_only=True)

    payment_account = serializers.SerializerMethodField(read_only=True)

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

    def get_currency_type(self, obj):
        value = CurrencyType.objects.first()
        '''
        Пока пользователи не настроены, отдаем так.
        Должно быть что-то вроде:
        player = request.user.player
        currency_types = CurrencyType.objects.filter(
                            country=player.location.country)
        '''
        return f'{value.currency_type}'

    def get_payment_account(self, obj):
        request = self.context.get('request', None)
        payment = Payment.objects.get(
            owner=request.user,
            payment_type=obj.payment_type
        )
        return payment.payment_account


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
