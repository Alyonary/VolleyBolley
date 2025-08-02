import base64

from django.core.files.base import ContentFile
from rest_framework import serializers

from .models import Favorite, Payment, Player, PlayerLocation


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


class PlayerLocationSerializer(serializers.ModelSerializer):
    """Serialize data for player location."""

    class Meta:
        model = PlayerLocation
        fields = ['country', 'city']


class PaymentSerializer(serializers.ModelSerializer):
    """Serialize payments data of player."""

    class Meta:
        model = Payment
        fields = ['payment_type', 'payment_account', 'is_preferred']


class PaymentsSerializer(serializers.Serializer):
    
    payments = PaymentSerializer(many=True)


class PlayerBaseSerializer(serializers.ModelSerializer):
    """Serialize data for model Player.
    
    Use only for actions with already registered player.
    """
    first_name = serializers.CharField(
        source='user.first_name',
        max_length=150,
        required=False
    )
    last_name = serializers.CharField(
        source='user.last_name',
        max_length=150,
        required=False
    )
    country = serializers.CharField(
        source='location.country',
        max_length=150,
        required=False
    )
    city = serializers.CharField(
        source='location.city',
        max_length=150,
        required=False
    )
    avatar = Base64ImageField(read_only=True)
    
    class Meta:
        model = Player
        fields = (
            'first_name',
            'last_name',
            'gender',
            'date_of_birth',
            'level',
            'country',
            'city',
            'avatar'
        )

    def update(self, instance, validated_data):

        user_data = validated_data.pop('user', {})
        for attr, value in user_data.items():
            setattr(instance.user, attr, value)
        
        location_data = validated_data.pop('location', {})
        for attr, value in location_data.items():
            setattr(instance.location, attr, value)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.user.save()
        instance.location.save()
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
        max_length=150,
        required=True
    )
    last_name = serializers.CharField(
        source='user.last_name',
        max_length=150,
        required=True
    )
    #TODO Переделать под новую модель
    country = serializers.CharField(
        source='location.country',
        max_length=150,
        required=True
    )
    #TODO переделать под новую модель
    city = serializers.CharField(
        source='location.city',
        max_length=150,
        required=True
    )
    
    class Meta:
        model = Player
        fields = (
            'first_name',
            'last_name',
            'gender',
            'date_of_birth',
            'level',
            'country',
            'city',
        )
        extra_kwargs = {
            'date_of_birth': {'required': True},
            'level': {'required': True},
            'gender': {'required': True},
        }


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

    def get_is_favorite(self):
        """Retrieve if player is in favorite list."""
        return Favorite.objects.filter(
            player=self.context.get('player'),
            favorite=self.player_id
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
