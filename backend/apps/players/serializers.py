import base64
from datetime import timedelta

from django.core.files.base import ContentFile
from django.core.validators import MinValueValidator
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from apps.event.models import Game, Tourney
from apps.players.constants import PlayerIntEnums
from apps.players.exceptions import (
    DuplicateVoteError,
    InvalidRatingError,
    ParticipationError,
    PlayerNotExistsError,
    PlayerNotIntError,
    RateCodeError,
    RatingLimitError,
    SelfRatingError,
)
from apps.players.models import (
    Favorite,
    Payment,
    Player,
    PlayerRating,
    PlayerRatingVote,
)
from apps.players.rating import GradeSystem


class Base64ImageField(serializers.ImageField):
    """Serialize images encoded in base64 format."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(
                base64.b64decode(imgstr), name='temp.' + ext
            )

        return super().to_internal_value(data)


class PaymentSerializer(serializers.ModelSerializer):
    """Serialize payment data of player."""

    class Meta:
        model = Payment
        fields = ['payment_type', 'payment_account', 'is_preferred']
        extra_kwargs = {
            'payment_type': {'required': True},
            'payment_account': {'required': True},
            'is_preferred': {'required': True}
        }


class PaymentsSerializer(serializers.Serializer):
    """Serialize all payment data of player."""

    payments = PaymentSerializer(many=True)

    def validate_payments(self, payments):
        """Validate that exactly one payment is preferred."""
        preferred_count = sum(
            1 for p in payments if p.get('is_preferred', False)
        )
        if preferred_count != 1:
            raise serializers.ValidationError(
                "Exactly one payment must be preferred."
            )

        return payments

    def update_or_create_payments(self, player):
        """Create or update payments for player."""
        errors = []
        updated_payments = []

        with transaction.atomic():
            for payment_data in self.validated_data['payments']:
                try:
                    payment, created = Payment.objects.update_or_create(
                        player=player,
                        payment_type=payment_data['payment_type'],
                        defaults=payment_data
                    )
                    updated_payments.append(payment)

                except Exception as e:
                    errors.append({
                        'payment_type': payment_data['payment_type'],
                        'error': str(e)
                    })

        if errors:
            raise serializers.ValidationError(
                {'errors': errors}
            )

        return updated_payments


class PlayerBaseSerializer(serializers.ModelSerializer):
    """Serialize data for model Player.

    Use only for actions with already registered player.
    """
    first_name = serializers.CharField(
        source='user.first_name',
        max_length=PlayerIntEnums.PLAYER_DATA_MAX_LENGTH.value,
        required=False
    )
    last_name = serializers.CharField(
        source='user.last_name',
        max_length=PlayerIntEnums.PLAYER_DATA_MAX_LENGTH.value,
        required=False
    )
    avatar = Base64ImageField(read_only=True)
    level = serializers.CharField(
        write_only=True,
        required=True
    )

    class Meta:
        model = Player
        fields = (
            'first_name',
            'last_name',
            'gender',
            'level',
            'date_of_birth',
            'country',
            'city',
            'avatar'
        )


    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['level'] = instance.rating.grade
        return rep

    def update(self, instance, validated_data):
        level = validated_data.pop('level', None)
        self._update_player_rate(instance, level)
        user_data = validated_data.pop('user', {})
        for attr, value in user_data.items():
            setattr(instance.user, attr, value)
        instance.user.save()
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.is_registered = True
        instance.save()
        return instance

    def _update_player_rate(self, player, new_level):
        """
        Check if PLayerRating object exists, create if not.
        Update grade if new_level is provided.
        """
        player_rate_obj, _ = PlayerRating.objects.get_or_create(player=player)
        if new_level: 
            player_rate_obj.grade = new_level
            player_rate_obj.save()
        return player_rate_obj


class AvatarSerializer(PlayerBaseSerializer):
    """Serialize avatar data for avatar managing."""

    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = Player
        fields = ('avatar', )


class PlayerAuthSerializer(PlayerBaseSerializer):
    """Serialize data of player after authentication."""
    player_id = serializers.PrimaryKeyRelatedField(
        source='id', read_only=True
    )

    class Meta:
        model = Player
        fields = (
            'player_id',
            'avatar',
            'first_name',
            'last_name',
            'gender',
            'date_of_birth',
            'level',
            'country',
            'city',
            'is_registered'
        )
        read_only_fields = (
            'player_id',
            'avatar',
            'first_name',
            'last_name',
            'gender',
            'date_of_birth',
            'level',
            'country',
            'city',
            'is_registered'
        )


class PlayerRegisterSerializer(PlayerBaseSerializer):
    """Serialize data for player registration."""

    first_name = serializers.CharField(
        source='user.first_name',
        max_length=PlayerIntEnums.PLAYER_DATA_MAX_LENGTH.value,
        required=True
    )
    last_name = serializers.CharField(
        source='user.last_name',
        max_length=PlayerIntEnums.PLAYER_DATA_MAX_LENGTH.value,
        required=True
    )


    class Meta:
        model = Player
        fields = (
            'first_name',
            'last_name',
            'gender',
            'level',
            'date_of_birth',
            'country',
            'city',
        )


class PlayerListSerializer(PlayerBaseSerializer):
    """Serialize player list data."""

    player_id = serializers.PrimaryKeyRelatedField(
        source='id', read_only=True
    )
    is_favorite = serializers.SerializerMethodField(
        read_only=True
    )
    
    class Meta:
        model = Player
        fields = (
            'player_id',
            'first_name',
            'last_name',
            'avatar',
            'level',
            'is_favorite'
        )
        read_only_fields = (
            'player_id',
            'first_name',
            'last_name',
            'avatar',
            'level',
            'is_favorite'
        )

    def get_is_favorite(self, obj):
        """Retrieve if player is in favorite list."""
        return Favorite.objects.filter(
            player=self.context.get('player'),
            favorite=self.context.get('favorite')
        ).exists()


class FavoriteSerializer(serializers.Serializer):
    """Serialize player data to add/delete player to/from favorite list."""

    def validate(self, data):
        """Validate that player can be added/deleted to/from favorite list."""
        player = self.context.get('player')
        favorite = self.context.get('favorite')
        request_method = self.context.get('request').method
        object_in_favorite_list = Favorite.objects.filter(
            player=player, favorite=favorite
        ).exists()
        if request_method == 'POST':
            if favorite == player:
                raise serializers.ValidationError(
                    'Error: You cannot add yourself to your favorite list.'
                )
            if object_in_favorite_list:
                raise serializers.ValidationError(
                    f'Error: You have already added player {favorite} '
                    'to your favorite list.'
                )
        elif request_method == 'DELETE':
            if not object_in_favorite_list:
                raise serializers.ValidationError(
                    f'Error: You do not have player {favorite} '
                    'in your favorite list.'
                )
        return data


class PlayerGameSerializer(PlayerAuthSerializer):
    """Player data for retrieve in event serializer."""
    level = serializers.CharField(
        source='rating.grade', read_only=True
    )
    class Meta:
        model = Player
        fields = (
            'player_id',
            'first_name',
            'last_name',
            'avatar',
            'level'
        )
        read_only_fields = (
            'player_id',
            'first_name',
            'last_name',
            'avatar',
            'level'
        )


class PlayerRateItemSerializer(serializers.Serializer):
    """
    Serializer for a single player rating action.

    Validates that the rater can rate the specified player, checks the limit
    of ratings within the last 2 months, and calculates the rating value
    based on the level change and coefficient table.
    Returns a dict with rater id, rated player id, and calculated value.
    """

    player_id = serializers.IntegerField(
        validators=[MinValueValidator(1)], 
        help_text="player_id must be a positive integer."
    )
    level_changed = serializers.ChoiceField(
        required=True,
        choices=[
            GradeSystem.UP,
            GradeSystem.DOWN,
            GradeSystem.CONFIRM]
    )

    def validate_level_changed(self, value):
        if not value or value not in [
            GradeSystem.UP,
            GradeSystem.DOWN,
            GradeSystem.CONFIRM
        ]:
            raise RateCodeError(
                "level_changed must be one of: 'UP', 'DOWN', 'CONFIRM'."
            )
        return value
    
    def validate(self, data):
        """
        Validates rating limits and calculates rating value for one player.
        """
        request = self.context.get('request')
        event: Game | Tourney = self.context.get('event')
        rater_player: Player = request.user.player
        
        try:
            rated_player = Player.objects.get(id=data['player_id'])
        except Player.DoesNotExist as e:
            raise PlayerNotExistsError(
                f"Player with id {data['player_id']} does not exist."
            ) from e

        if rater_player == rated_player:
            raise SelfRatingError(
                "You cannot rate yourself."
            )
        
        if not event.players.filter(id=rater_player.id).exists():
            raise ParticipationError(
                "You can rate only players in events you participated in."
            )
        
        if not event.players.filter(id=rated_player.id).exists():
            raise ParticipationError(
                f"You can rate only players in events you participated in. "
                f"Player {rated_player.user.username} did not participate "
                "in this event."
            )
        
        if PlayerRatingVote.objects.filter(
            rater=rater_player,
            rated=rated_player,
            game=event if isinstance(event, Game) else None,
            tourney=event if isinstance(event, Tourney) else None,
        ).exists():
            raise DuplicateVoteError(
                f"You have already rated player {rated_player.user.username} "
                "in this event."
            )
        
        two_months_ago = timezone.now() - timedelta(
            days=PlayerIntEnums.PLAYER_VOTE_LIMIT.value
        )
        last_votes = PlayerRatingVote.objects.filter(
            rater=rater_player,
            rated=rated_player,
            created_at__gte=two_months_ago
        )
        if last_votes.count() >= 2:
            raise RatingLimitError(
                f"You have already rated player {rated_player.user.username} "
                "2 times in the last 2 months."
            )
        try:
            value = GradeSystem.get_value(
                rater = rater_player,
                rated = rated_player,
                level_change = data['level_changed']
            ) 
            return {
                'rater': rater_player.id,
                'rated_player': rated_player.id,
                'value': value
            }
        except InvalidRatingError as e:
            raise e

class PlayerRateSerializer(serializers.Serializer):
    """
    Serializer for bulk player rating actions.

    Accepts a list of player rating actions, validates each using
    PlayerRateItemSerializer, and creates PlayerRatingVote objects in bulk.
    Returns a list of dicts with rater id, rated player id, and rating value.
    """

    players = serializers.ListField(
        child=serializers.DictField(),
        allow_empty=False
    )

    def validate_players(self, players_data):
        """Validate each player item and filter out valid ones."""
        valid_items = []
        for item_data in players_data:
            try:
                item_serializer = PlayerRateItemSerializer(
                    data=item_data,
                    context=self.context
                )
                if item_serializer.is_valid(raise_exception=True):
                    valid_items.append(item_serializer.validated_data)
            except PlayerNotIntError as e:
                raise serializers.ValidationError(
                    "player_id must be a positive integer."
                ) from e
            except RateCodeError as e:
                raise serializers.ValidationError(
                    "level_changed must be one of: 'UP', 'DOWN', 'CONFIRM'."
                ) from e
            except (PlayerNotExistsError, 
                    SelfRatingError, 
                    ParticipationError, 
                    DuplicateVoteError, 
                    RatingLimitError,
                    InvalidRatingError):
                continue
            except serializers.ValidationError as e:
                raise e
        return valid_items

    def create(self, validated_data):
        """Bulk creates PlayerRatingVote objects for all valid ratings."""
        votes = []
        results = []
        event = self.context.get('event')
        for item in validated_data['players']:
            rater_player = Player.objects.get(id=item['rater'])
            rated_player = Player.objects.get(id=item['rated_player'])
            model_data = {
                'rater': rater_player,
                'rated': rated_player,
                'value': item['value'],
            }
            if isinstance(event, Game):
                model_data['game'] = event
            elif isinstance(event, Tourney):
                model_data['tourney'] = event
            vote = PlayerRatingVote(**model_data)
            votes.append(vote)
            results.append({
                'rater': item['rater'],
                'rated_player': item['rated_player'],
                'value': item['value']
            })
        
        if votes:
            PlayerRatingVote.objects.bulk_create(votes)
        return {'players': results}


class PlayerShortSerializer(serializers.ModelSerializer):
    """Serialize short player data for list of players in event."""
    player_id = serializers.IntegerField(source='id')
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    avatar = serializers.ImageField(allow_null=True)
    level = serializers.CharField(source='rating.grade', read_only=True)

    class Meta:
        model = Player
        fields = (
            'player_id',
            'first_name',
            'last_name',
            'avatar',
            'level',
        )
