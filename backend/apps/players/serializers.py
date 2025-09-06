import base64
from datetime import datetime, timedelta, timezone

from django.core.files.base import ContentFile
from django.db import transaction
from rest_framework import serializers

from apps.event.models import Game, Tourney
from apps.players.constants import PlayerIntEnums
from apps.players.models import Favorite, Payment, Player, PlayerRatingVote
from apps.players.rating import PlayerLevelGrade


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
    level = serializers.PrimaryKeyRelatedField(
        source='rating.grade', read_only=True
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

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        for attr, value in user_data.items():
            setattr(instance.user, attr, value)
            
        instance.user.save()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.is_registered = True
        
        instance.save()
        
        return instance



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
    level = serializers.PrimaryKeyRelatedField(
        source='rating.grade', read_only=True
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
            'date_of_birth',
            'country',
            'city',
        )

    def create(self, validated_data):
        level = validated_data.pop('level', None)
        player = Player.objects.create(**validated_data)
        player.level = level
        return player


class PlayerListSerializer(PlayerBaseSerializer):
    """Serialize player list data."""

    player_id = serializers.PrimaryKeyRelatedField(
        source='id', read_only=True
    )
    is_favorite = serializers.SerializerMethodField(
        read_only=True
    )
    level = serializers.PrimaryKeyRelatedField(
        source='rating.grade', read_only=True
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


class FavoriteSerializer(PlayerListSerializer):
    """Serialize player data to add/delete player to/from favorite list."""

    def validate(self, data):
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


class PlayerRateItemSerializer(serializers.Serializer):
    """
    Serializer for a single player rating action.

    Validates that the rater can rate the specified player, checks the limit
    of ratings within the last 2 months, and calculates the rating value
    based on the level change and coefficient table.
    Returns a dict with rater id, rated player id, and calculated value.
    """

    player_id = serializers.IntegerField()
    level_changed = serializers.ChoiceField(
        choices=[
            PlayerLevelGrade.UP,
            PlayerLevelGrade.DOWN,
            PlayerLevelGrade.CONFIRM]
    )

    def validate(self, data):
        """
        Validates rating limits and calculates rating value for one player.
        """
        request = self.context.get('request')
        if not request or not hasattr(request.user, 'player'):
            raise serializers.ValidationError('Invalid rater player.')
        rater_player: Player = request.user.player
        try:
            rated_player = Player.objects.get(id=data['player_id'])
        except Player.DoesNotExist as e:
            raise serializers.ValidationError(
                f"Player with id {data['player_id']} does not exist."
            ) from e
        # мб убрать?
        two_months_ago = timezone.now() - timedelta(days=60)
        last_votes = PlayerRatingVote.objects.filter(
            rater=rater_player,
            rated=rated_player,
            created_at__gte=two_months_ago
        )
        if last_votes.count() >= 2:
            raise serializers.ValidationError(
                f"You have already rated player {rated_player.user.username} "
                "2 times in the last 2 months."
            )
        value = PlayerLevelGrade.get_value(
            rater = rater_player,
            rated = rated_player,
            level_change = data['level_changed']
            
        ) 
        return {
            'rater': rater_player.id,
            'rated_player': rated_player.id,
            'value': value
        }


class PlayerRateSerializer(serializers.Serializer):
    """
    Serializer for bulk player rating actions.

    Accepts a list of player rating actions, validates each using
    PlayerRateItemSerializer, and creates PlayerRatingVote objects in bulk.
    Returns a list of dicts with rater id, rated player id, and rating value.
    """

    players = PlayerRateItemSerializer(many=True)

    def create(self, validated_data):
        """
        Bulk creates PlayerRatingVote objects for all valid ratings.

        Returns a list of dicts with rater id, rated player id, and value.
        """
        votes = []
        results = []
        for item in validated_data['players']:
            rater_player = Player.objects.get(id=item['rater'])
            rated_player = Player.objects.get(id=item['rated_player'])
            vote = PlayerRatingVote(
                rater=rater_player,
                rated=rated_player,
                value=item['value']
            )
            votes.append(vote)
            results.append({
                'rater': item['rater'],
                'rated_player': item['rated_player'],
                'value': item['value']
            })
        PlayerRatingVote.objects.bulk_create(votes)
        return results

    @classmethod
    def get_players_to_rate(
        cls,
        rater_player: Player,
        event: Game | Tourney
    ) -> list[Player]:
        """
        Returns a list of players whom rater_player can still rate
        (not more than 2 ratings in the last 2 months).
        """
        two_months_ago = datetime.now() - timedelta(days=60)
        available_players = []
        for player in event.players.all().exclude(id=rater_player.id):
            votes_count = PlayerRatingVote.objects.filter(
                rater=rater_player,
                rated=player,
                created_at__gte=two_months_ago
            ).count()
            if votes_count < 2:
                available_players.append(player)
        return available_players

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
