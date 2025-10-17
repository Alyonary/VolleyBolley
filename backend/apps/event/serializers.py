from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers as s

from apps.core.constants import GenderChoices
from apps.core.models import CurrencyType, GameLevel
from apps.courts.models import Court
from apps.courts.serializers import LocationSerializer
from apps.event.enums import EventIntEnums
from apps.event.models import Game, GameInvitation, Tourney, TourneyTeam
from apps.players.models import Payment, Player
from apps.players.serializers import PlayerGameSerializer


class BaseEventSerializer(s.ModelSerializer):

    start_time = s.DateTimeField(format='iso-8601')

    end_time = s.DateTimeField(format='iso-8601')

    levels = s.SlugRelatedField(
        slug_field='name',
        queryset=GameLevel.objects.all(),
        source='player_levels',
        many=True
    )

    gender = s.ChoiceField(choices=GenderChoices.choices)

    currency_type = s.CharField(
        required=False
    )

    payment_account = s.CharField(
        required=False
    )

    maximum_players = s.IntegerField(
        source='max_players',
    )

    def get_currency_type(self):
        """Returns the type of currency by the player's country."""
        host = self.context['request'].user.player
        try:
            currency_type = CurrencyType.objects.get(
                country=host.country)
        except CurrencyType.DoesNotExist as e:
            raise s.ValidationError(
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
            raise s.ValidationError(
                'No payment account found for this payment type')
        elif payment.payment_account is None:
            return 'Not defined'
        else:
            return payment.payment_account

    def validate_maximum_players(self, value):
        minimal = EventIntEnums.MIN_PLAYERS.value
        maximal = EventIntEnums.MAX_PLAYERS.value
        if not (minimal <= value <= maximal):
            raise s.ValidationError(
                f'Number of players must be between {minimal} and {maximal}!')
        return value

    def validate(self, value):
        start_time = value.get('start_time')
        end_time = value.get('end_time')
        if start_time < timezone.now():
            raise s.ValidationError(
                'Game start time can be in future.')
        elif end_time < start_time:
            raise s.ValidationError(
                'The end time of the game must be later than the start time.')
        elif not start_time.tzinfo or not end_time.tzinfo:
            raise s.ValidationError(
                'Time must include timezone information')
        return value


class BaseGameSerializer(BaseEventSerializer):
    game_id = s.IntegerField(source='pk', read_only=True)

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


class GameSerializer(BaseGameSerializer):
    """Uses for create requests."""

    players = s.PrimaryKeyRelatedField(
        queryset=Player.objects.all(),
        many=True,
        required=False
    )
    court_id = s.PrimaryKeyRelatedField(
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

        game = Game.objects.create(
            currency_type=self.get_currency_type(),

            payment_account=self.get_payment_account(
                validated_data['payment_type']
            ),
            **validated_data)

        game.players.add(host)
        game.player_levels.set(levels)
        game_ct = ContentType.objects.get_for_model(Game)
        for player in players:
            serializer = GameInviteSerializer(
                data={
                    'host': game.host.id,
                    'invited': player.id,
                    "content_type": game_ct.id,
                    "object_id": game.id
                },
                context=self.context
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
        return game

    def validate_players(self, value):
        host = self.context['request'].user.player
        if host in value:
            raise s.ValidationError(
                'You can not invite yourself.')
        if len(value) != len(set(value)):
            raise s.ValidationError(
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


class GameInviteSerializer(s.ModelSerializer):
    invited = s.PrimaryKeyRelatedField(
        write_only=True, queryset=Player.objects.all())

    class Meta:
        model = GameInvitation
        fields = ('host', 'invited', 'content_type', 'object_id')
        write_only_fields = fields
        validators = [
            s.UniqueTogetherValidator(
                queryset=GameInvitation.objects.all(),
                fields=('host', 'invited', 'content_type', 'object_id'),
                message=_('This invitation already exists!'),
            )
        ]

    def validate(self, attrs):
        host = attrs.get('host')
        invited = attrs.get('invited')
        content_type = attrs.get('content_type')
        event = content_type.get_object_for_this_type(
            pk=attrs.get('object_id'))

        levels = [level.name for level in event.player_levels.all()]

        if isinstance(event, Game):
            players = event.players.all()
        elif isinstance(event, Tourney):
            player_ids = event.teams.all().values_list('players', flat=True)
            players = Player.objects.filter(id__in=player_ids)
        else:
            raise s.ValidationError(
                {'content_type': (f'{content_type.model_class()}'
                                  ' is unknown object class.')}
            )

        if host == invited:
            raise s.ValidationError(
                {'invited': 'You can not invite yourself.'})
        elif invited in players:
            raise s.ValidationError(
                {'invited': 'This player is already participate in the game.'})
        elif invited.rating.grade not in levels:
            raise s.ValidationError(
                {'invited': f'Level of the player {invited.rating.grade} '
                 'not allowed in this game. '
                 f'Allowed levels: {", ".join(levels)}'})
        return attrs


class GameShortSerializer(s.ModelSerializer):
    game_id = s.IntegerField(source='pk')

    host = PlayerGameSerializer()

    court_location = LocationSerializer(source='court.location')

    start_time = s.DateTimeField(format='iso-8601')

    end_time = s.DateTimeField(format='iso-8601')

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
        read_only_fields = fields


class TourneyTeamSerializer(s.Serializer):

    team_id = s.IntegerField(source='id')
    players = s.PrimaryKeyRelatedField(
        queryset=Player.objects.all(), many=True)

    class Meta:
        model = TourneyTeam
        fields = ['team_id', 'players']
        read_only_fields = fields


class BaseTourneySerializer(BaseEventSerializer):
    tournament_id = s.IntegerField(source='pk', read_only=True)
    is_individual = s.BooleanField()
    maximum_teams = s.IntegerField(required=False, allow_null=True)
    maximum_players = s.IntegerField(source='max_players', allow_null=True)

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

    def validate_maximum_teams(self, value):
        minimal = EventIntEnums.MIN_TEAMS.value
        maximal = EventIntEnums.MAX_TEAMS.value
        if value is not None and not (minimal <= value <= maximal):
            raise s.ValidationError(
                f'Number of teams must be between {minimal} and {maximal}!')
        return value

    def validate_maximum_players(self, value):
        if value is None:
            return value
        return super().validate_maximum_players(value)


class TourneySerializer(BaseTourneySerializer):
    """Used for tournament creation."""

    players = s.PrimaryKeyRelatedField(
        queryset=Player.objects.all(),
        many=True,
        required=False,
        write_only=True
    )
    court_id = s.PrimaryKeyRelatedField(
        source='court',
        queryset=Court.objects.all()
    )
    teams = TourneyTeamSerializer(many=True, read_only=True)

    class Meta(BaseTourneySerializer.Meta):
        model = BaseTourneySerializer.Meta.model
        fields = BaseTourneySerializer.Meta.fields + [
            'court_id',
            'teams',
            'players'
        ]

    def validate(self, attrs):
        if attrs['is_individual']:
            attrs['maximum_teams'] = 1
            if attrs['max_players'] is None:
                raise s.ValidationError(
                    {'maximum_players': 'The value must be integer.'}
                )
        else:
            if attrs['maximum_teams'] is None:
                raise s.ValidationError(
                    {'maximum_teams': 'The value must be integer.'}
                )
            attrs['max_players'] = attrs[
                'maximum_teams'] * EventIntEnums.TOURNEY_TEAM_CAPACITY
        return attrs

    def create(self, validated_data):
        host = self.context['request'].user.player
        validated_data['host'] = host
        players = validated_data.pop('players')
        levels = validated_data.pop('player_levels')

        tourney = Tourney.objects.create(
            currency_type=self.get_currency_type(),

            payment_account=self.get_payment_account(
                validated_data['payment_type']
            ),
            **validated_data)

        max_teams = int(validated_data['maximum_teams'])
        for _x in range(max_teams):
            team = TourneyTeam.objects.create(tourney=tourney)
            if _x == 0:
                team.players.add(host)

        tourney.player_levels.set(levels)
        tourney_ct = ContentType.objects.get_for_model(Tourney)
        for player in players:
            serializer = GameInviteSerializer(
                data={
                    'host': tourney.host.id,
                    'invited': player.id,
                    "content_type": tourney_ct.id,
                    "object_id": tourney.id
                },
                context=self.context
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()

        return tourney

    # def validate_players(self, value):
    #     host = self.context['request'].user.player
    #     if host in value:
    #         raise s.ValidationError(
    #             'You can not invite yourself.')
    #     if len(value) != len(set(value)):
    #         raise s.ValidationError(
    #             'The players should not repeat themselves.')
    #     return value


# class TourneyDetailSerializer(BaseTourneySerializer):
#     """Serializer for viewing tournament details."""

#     host = PlayerGameSerializer()
#     court_location = LocationSerializer(source='court.location')
#     players = PlayerGameSerializer(many=True)

#     class Meta(BaseTourneySerializer.Meta):
#         model = BaseTourneySerializer.Meta.model
#         fields = BaseTourneySerializer.Meta.fields + [
#             'host',
#             'court_location',
#             'players'
#         ]


# class TourneyShortSerializer(s.ModelSerializer):
#     tournament_id = s.IntegerField(source='pk')
#     host = PlayerGameSerializer()
#     court_location = LocationSerializer(source='court.location')
#     start_time = s.DateTimeField(format='iso-8601')
#     end_time = s.DateTimeField(format='iso-8601')

#     class Meta:
#         model = Tourney
#         fields = [
#             'tournament_id',
#             'host',
#             'court_location',
#             'message',
#             'start_time',
#             'end_time'
#         ]
#         read_only_fields = fields
