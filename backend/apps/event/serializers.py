from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from apps.core.constants import GenderChoices
from apps.core.models import CurrencyType, GameLevel
from apps.courts.models import Court
from apps.courts.serializers import LocationSerializer
from apps.event.enums import EventIntEnums
from apps.event.models import Game, GameInvitation
from apps.players.models import Payment, Player
from apps.players.serializers import PlayerGameSerializer


class BaseGameSerializer(serializers.ModelSerializer):

    game_id = serializers.IntegerField(source='pk', read_only=True)

    start_time = serializers.DateTimeField(format='iso-8601')

    end_time = serializers.DateTimeField(format='iso-8601')

    levels = serializers.SlugRelatedField(
        slug_field='name',
        queryset=GameLevel.objects.all(),
        source='player_levels',
        many=True
    )

    gender = serializers.ChoiceField(choices=GenderChoices.choices)

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

    def validate_maximum_players(self, value):
        minimal = EventIntEnums.MIN_PLAYERS.value
        maximal = EventIntEnums.MAX_PLAYERS.value
        if not (minimal <= value <= maximal):
            raise serializers.ValidationError(
                f'Number of players must be between {minimal} and {maximal}!')
        return value

    def validate(self, value):
        request = self.context.get('request', None)
        player = request.user.player
        if value.get('payment_type') == 'CASH':
            value['payment_account'] = 'Cash money'
        else:
            payment = Payment.objects.filter(
                player=player,
                payment_type=value.get('payment_type')
            ).last()
            if not payment:
                raise serializers.ValidationError(
                    'No payment account found for this payment type')
            if payment.payment_account is None:
                value['payment_account'] = 'Not defined'
            else:
                value['payment_account'] = payment.payment_account
        currency_type = CurrencyType.objects.filter(
                            country=player.country).first()
        value['currency_type'] = currency_type
        start_time = value.get('start_time')
        end_time = value.get('end_time')
        if start_time < timezone.now():
            raise serializers.ValidationError(
                'Game start time can be in future.')
        elif end_time < start_time:
            raise serializers.ValidationError(
                'The end time of the game must be later than the start time.')
        elif not start_time.tzinfo or not end_time.tzinfo:
            raise serializers.ValidationError(
                'Time must include timezone information')
        return value


class GameSerializer(BaseGameSerializer):
    """Uses for create requests."""

    players = serializers.PrimaryKeyRelatedField(
        queryset=Player.objects.all(),
        many=True,
        required=False
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
        host = self.context['request'].user.player
        validated_data['host'] = host
        players = validated_data.pop('players')
        levels = validated_data.pop('player_levels')
        game = Game.objects.create(**validated_data)
        game.players.add(host)
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
        host = self.context['request'].user.player
        if host in value:
            raise serializers.ValidationError(
                'You can not invite yourself.')
        if len(value) != len(set(value)):
            raise serializers.ValidationError(
                'The players should not repeat themselves.')
        return value


class GameDetailSerializer(BaseGameSerializer):
    """Game serializer uses for retrieve requests."""

    host = PlayerGameSerializer()

    game_type = serializers.SerializerMethodField(read_only=True)

    court_location = LocationSerializer(source='court.location')

    players = PlayerGameSerializer(many=True)

    class Meta(BaseGameSerializer.Meta):
        model = BaseGameSerializer.Meta.model
        fields = BaseGameSerializer.Meta.fields + [
            'game_type',
            'host',
            'court_location',
            'players'
        ]

    def get_game_type(self, obj):
        """Assigns a type to the game.
        Returning values:
        MY GAMES, UPCOMING, ARCHIVE, INVITES, ACTIVE.
        """
        request = self.context.get('request', None)
        if obj.host == request.user.player:
            return 'MY GAMES'
        elif GameInvitation.objects.filter(
                invited=request.user.player, game=obj).exists():
            return 'INVITES'
        elif obj.end_time < timezone.now():
            return 'ARCHIVE'
        elif obj.start_time > timezone.now():
            return 'UPCOMING'
        else:
            return 'ACTIVE'


class GameInviteSerializer(serializers.ModelSerializer):

    invited = serializers.PrimaryKeyRelatedField(
        write_only=True, queryset=Player.objects.all())

    class Meta:
        model = GameInvitation
        fields = ('host', 'invited', 'game')
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=GameInvitation.objects.all(),
                fields=('host', 'invited', 'game'),
                message=_('This invitation already exists!'),
            )
        ]

    def validate(self, attrs):
        host = attrs.get('host')
        invited = attrs.get('invited')
        game = attrs.get('game')
        if host == invited:
            raise serializers.ValidationError(
                'You can not invite yourself.')
        elif invited in game.players.all():
            raise serializers.ValidationError(
                'This player is already participating in the game.')
        return attrs


class TourneySerializer(serializers.ModelSerializer):
    pass


class GameShortSerializer(serializers.ModelSerializer):

    game_id = serializers.IntegerField(source='pk', read_only=True)

    host = PlayerGameSerializer()

    court_location = LocationSerializer(source='court.location')

    start_time = serializers.DateTimeField(format='iso-8601')

    end_time = serializers.DateTimeField(format='iso-8601')

    class Meta:
        model = Game
        fields = [
            'game_id',
            'host',
            'court_location',
            'message',
            'start_time',
            'end_time'
        ]
