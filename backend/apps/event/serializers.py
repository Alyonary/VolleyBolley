from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from apps.core.constants import GenderChoices
from apps.core.models import CurrencyType, GameLevel
from apps.courts.models import Court
from apps.courts.serializers import LocationSerializer
from apps.event.enums import EventIntEnums
from apps.event.models import Game, GameInvitation, Tourney
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

    def get_currency_type(self):
        """Returns the type of currency by the player's country."""
        host = self.context['request'].user.player
        try:
            currency_type = CurrencyType.objects.get(
                country=host.country)
        except CurrencyType.DoesNotExist as e:
            raise serializers.ValidationError(
                f"{e}: Валюта для страны {host.country} не найдена.") from e
        return currency_type

    def get_payment_account(self, payment_type):
        """Returns the payment account to the player's payment type."""
        player = self.context['request'].user.player
        if payment_type == 'CASH':
            return 'Cash money'
        payment = Payment.objects.filter(
            player=player,
            payment_type=payment_type
        ).last()
        if payment is None:
            raise serializers.ValidationError(
                'No payment account found for this payment type')
        elif payment.payment_account is None:
            return 'Not defined'
        else:
            return payment.payment_account

    def create(self, validated_data):
        host = self.context['request'].user.player
        validated_data['host'] = host
        players = validated_data.pop('players')
        levels = validated_data.pop('player_levels')

        game = Game.objects.create(
            currency_type=self.get_currency_type(),

            payment_account=self.get_payment_account(
                validated_data['payment_type']
            ),
            **validated_data)

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

    court_location = LocationSerializer(source='court.location')

    players = PlayerGameSerializer(many=True)

    class Meta(BaseGameSerializer.Meta):
        model = BaseGameSerializer.Meta.model
        fields = BaseGameSerializer.Meta.fields + [
            'host',
            'court_location',
            'players'
        ]


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
        levels = [level.name for level in game.player_levels.all()]
        if host == invited:
            raise serializers.ValidationError(
                {'invited': 'You can not invite yourself.'})
        elif invited in game.players.all():
            raise serializers.ValidationError(
                {'invited': 'This player is already participate in the game.'})
        elif invited.rating.grade not in levels:
            raise serializers.ValidationError(
                {'invited': f'Level of the player {invited.rating.grade} '
                 'not allowed in this game. '
                 f'Allowed levels: {", ".join(levels)}'})
        return attrs


class GameShortSerializer(serializers.ModelSerializer):
    game_id = serializers.IntegerField(source='pk')

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
        read_only_fields = [
            'game_id',
            'host',
            'court_location',
            'message',
            'start_time',
            'end_time'
        ]


class BaseTourneySerializer(serializers.ModelSerializer):
    tournament_id = serializers.IntegerField(source='pk', read_only=True)
    start_time = serializers.DateTimeField(format='iso-8601')
    end_time = serializers.DateTimeField(format='iso-8601')
    levels = serializers.SlugRelatedField(
        slug_field='name',
        queryset=GameLevel.objects.all(),
        source='player_levels',
        many=True
    )
    gender = serializers.ChoiceField(choices=GenderChoices.choices)
    currency_type = serializers.CharField(required=False)
    payment_account = serializers.CharField(required=False)
    maximum_players = serializers.IntegerField(source='max_players')

    class Meta:
        model = Tourney
        fields = [
            'tournament_id',
            'message',
            'start_time',
            'end_time',
            'is_individual',
            'gender',
            'levels',
            'maximum_players',
            'maximum_teams',
            'price_per_person',
            'currency_type',
            'payment_type',
            'payment_account',
        ]


class TourneySerializer(BaseTourneySerializer):
    """Used for tournament creation."""

    players = serializers.PrimaryKeyRelatedField(
        queryset=Player.objects.all(),
        many=True,
        required=False
    )
    court_id = serializers.PrimaryKeyRelatedField(
        source='court',
        queryset=Court.objects.all()
    )

    class Meta(BaseTourneySerializer.Meta):
        model = BaseTourneySerializer.Meta.model
        fields = BaseTourneySerializer.Meta.fields + [
            'court_id',
            'players'
        ]

    def create(self, validated_data):
        request = self.context.get('request')

        if not request or not hasattr(request.user, 'player'):
            from apps.players.models import Player
            host = Player.objects.first()
        else:
            host = request.user.player

        validated_data['host'] = host
        players = validated_data.pop('players', [])
        levels = validated_data.pop('player_levels', [])
        validated_data.pop('currency_type', None)
        validated_data.pop('payment_account', None)

        tourney = Tourney.objects.create(
            currency_type=self.get_currency_type(host),
            payment_account=self.get_payment_account(
                host, validated_data['payment_type']
            ),
            **validated_data
        )

        tourney.players.add(host, *players)
        tourney.player_levels.set(levels)
        return tourney

    def get_currency_type(self, host):
        try:
            return CurrencyType.objects.get(country=host.country)
        except CurrencyType.DoesNotExist as e:
            raise serializers.ValidationError(
                f'{e}: Currency for country {host.country} was not found.'
            ) from e

    def get_payment_account(self, host, payment_type):
        if payment_type == 'CASH':
            return 'Cash money'
        payment = Payment.objects.filter(
            player=host, payment_type=payment_type
        ).last()
        if payment is None:
            raise serializers.ValidationError(
                'No payment account found for this payment type'
            )
        elif payment.payment_account is None:
            return 'Not defined'
        else:
            return payment.payment_account


class TourneyDetailSerializer(BaseTourneySerializer):
    """Serializer for viewing tournament details."""

    host = PlayerGameSerializer()
    court_location = LocationSerializer(source='court.location')
    players = PlayerGameSerializer(many=True)

    class Meta(BaseTourneySerializer.Meta):
        model = BaseTourneySerializer.Meta.model
        fields = BaseTourneySerializer.Meta.fields + [
            'host',
            'court_location',
            'players'
        ]


class TourneyShortSerializer(serializers.ModelSerializer):
    tournament_id = serializers.IntegerField(source='pk')
    host = PlayerGameSerializer()
    court_location = LocationSerializer(source='court.location')
    start_time = serializers.DateTimeField(format='iso-8601')
    end_time = serializers.DateTimeField(format='iso-8601')

    class Meta:
        model = Tourney
        fields = [
            'tournament_id',
            'host',
            'court_location',
            'message',
            'start_time',
            'end_time'
        ]
        read_only_fields = fields
