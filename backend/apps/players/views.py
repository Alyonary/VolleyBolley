from django.contrib.auth.models import AnonymousUser
from django.db.models import Exists, OuterRef, Prefetch
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from apps.core.permissions import IsNotRegisteredPlayer, IsRegisteredPlayer
from apps.event.models import Game
from apps.players.constants import PlayerIntEnums
from apps.players.models import Favorite, Payment, Player
from apps.players.serializers import (
    AvatarSerializer,
    FavoriteSerializer,
    PaymentSerializer,
    PaymentsSerializer,
    PlayerBaseSerializer,
    PlayerKeyDetailSerializer,
    PlayerListSerializer,
    PlayerRegisterSerializer,
)
from apps.players.swagger_schemas import (
    AVATAR_ME_PUT_SCHEMA,
    FAVORITE_DELETE_SCHEMA,
    FAVORITE_POST_SCHEMA,
    PAYMENTS_ME_GET_SCHEMA,
    PAYMENTS_ME_PUT_SCHEMA,
    PLAYER_DETAIL_SCHEMA,
    PLAYER_LIST_SCHEMA,
    PLAYERS_ME_DELETE_SCHEMA,
    PLAYERS_ME_PATCH_SCHEMA,
    PLAYERS_ME_SCHEMA,
    PLAYERS_REGISTER_SCHEMA,
)
from apps.users.models import User


class PlayerViewSet(ReadOnlyModelViewSet):
    queryset = (
        Player.objects.select_related('country', 'city', 'user')
        .prefetch_related('payments', 'player', 'favorite', 'rating')
        .all()
    )
    serializer_class = PlayerBaseSerializer
    http_method_names = ['get', 'post', 'patch', 'put', 'delete']
    permission_classes = [IsRegisteredPlayer]

    def get_serializer_class(self, *args, **kwargs):
        if self.action == 'me':
            return PlayerBaseSerializer
        if self.action == 'put_delete_avatar':
            return AvatarSerializer
        if self.action == 'register':
            return PlayerRegisterSerializer
        if self.action == 'get_put_payments':
            if self.request.method == 'GET':
                return PaymentsSerializer
            return PaymentSerializer
        if self.action == 'list':
            return PlayerListSerializer
        if self.action == 'retrieve':
            return PlayerKeyDetailSerializer
        if self.action == 'favorite':
            return FavoriteSerializer
        return super().get_serializer_class(*args, **kwargs)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        user = self.request.user
        if not isinstance(user, AnonymousUser):
            context.update(
                {
                    'player': self.queryset.filter(
                        user=self.request.user
                    ).first(),
                    'current_user': self.request.user,
                }
            )
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        current_player = None
        if not isinstance(self.request.user, AnonymousUser):
            current_player = self.request.user.player

        if self.action != 'register':
            queryset.exclude(is_registered=False)

        if self.action == 'retrieve':
            player_id = self.kwargs.get('pk')
            if player_id:
                player = queryset.get(pk=player_id)
                if player and player.is_registered is True:
                    return (
                        Player.objects.filter(pk=player_id)
                        .select_related('country', 'city', 'user')
                        .prefetch_related(
                            'player',
                            'favorite',
                            'rating',
                            Prefetch(
                                'games_players',
                                Game.objects.recent_games(
                                    player=player,
                                    limit=PlayerIntEnums.RECENT_ACTIVITIES_LENGTH,
                                ).select_related('court__location'),
                                to_attr='recent_games',
                            ),
                        )
                        .all()
                    )
            return None

        if self.action == 'get_put_payments':
            if current_player.is_registered:
                return Payment.objects.filter(player=current_player)
            return None

        if self.action == 'list':
            queryset = queryset.exclude(user=self.request.user)
            is_favorite_subquery = Favorite.objects.filter(
                player=current_player, favorite=OuterRef('pk')
            )
            queryset.annotate(
                is_favorite=Exists(is_favorite_subquery)
            ).order_by('-is_favorite', 'user__first_name')

        return queryset

    def get_object(self):
        if self.action in ['me', 'register', 'put_delete_avatar', 'favorite']:
            obj = get_object_or_404(
                self.queryset.filter(user=self.request.user)
            )
            self.check_object_permissions(self.request, obj)

            return obj

        return super().get_object()

    @swagger_auto_schema(**PLAYER_LIST_SCHEMA)
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(**PLAYER_DETAIL_SCHEMA)
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        serializer = PlayerKeyDetailSerializer(
            instance={'player': instance},
            context={
                'request': request,
            },
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(**PLAYERS_ME_SCHEMA)
    @swagger_auto_schema(**PLAYERS_ME_PATCH_SCHEMA)
    @swagger_auto_schema(**PLAYERS_ME_DELETE_SCHEMA)
    @action(['GET', 'PATCH', 'DELETE'], detail=False)
    def me(self, request):
        """Get, patch or delete current player."""
        instance = self.get_object()
        if self.request.method == 'DELETE':
            user = User.objects.filter(player=instance)
            if user:
                # After that corresponding player object will be deleted
                # automatically
                user.delete()

                return Response(status=status.HTTP_204_NO_CONTENT)

            raise Response(status=status.HTTP_404_NOT_FOUND)

        if self.request.method == 'PATCH':
            serializer = self.get_serializer(
                instance, data=request.data, partial=True
            )
            if serializer.is_valid(raise_exception=True):
                serializer.save()

                return Response(status=status.HTTP_200_OK)

            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(instance)

        return Response(status=status.HTTP_200_OK, data=serializer.data)

    @swagger_auto_schema(**AVATAR_ME_PUT_SCHEMA)
    @action(
        detail=False,
        methods=['PUT'],
        url_path='me/avatar',
        url_name='me-avatar',
    )
    def put_delete_avatar(self, request):
        """Update avatar.
        To delete avatar set its value to null.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()

            return Response(data=serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(**PAYMENTS_ME_GET_SCHEMA)
    @swagger_auto_schema(**PAYMENTS_ME_PUT_SCHEMA)
    @action(
        detail=False,
        methods=['PUT', 'GET'],
        url_path='me/payments',
        url_name='me-payments',
    )
    def get_put_payments(self, request):
        """Get or put payment data of player."""
        if self.request.method == 'GET':
            payments = {'payments': self.get_queryset()}
            serializer = self.get_serializer(payments)

            return Response(data=serializer.data, status=status.HTTP_200_OK)

        serializer = PaymentsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.update_or_create_payments(request.user.player)

        return Response(status=status.HTTP_200_OK)

    @swagger_auto_schema(**FAVORITE_POST_SCHEMA)
    @swagger_auto_schema(**FAVORITE_DELETE_SCHEMA)
    @action(detail=True, methods=['POST', 'DELETE'])
    def favorite(self, request, pk=None):
        """Add or delete player from favorite list."""
        player = self.get_object()
        favorite = get_object_or_404(Player, id=pk)
        serializer = FavoriteSerializer(
            data=request.data,
            context={
                'request': request,
                'player': player,
                'favorite': favorite,
            },
        )
        serializer.is_valid(raise_exception=True)
        if request.method == 'POST':
            Favorite.objects.create(player=player, favorite=favorite)
            response_serializer = FavoriteSerializer(
                favorite,
                context={
                    'request': request,
                    'player': player,
                    'favorite': favorite,
                },
            )
            return Response(
                response_serializer.data, status=status.HTTP_201_CREATED
            )

        instance = get_object_or_404(
            Favorite, player=player, favorite=favorite
        )
        instance.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(**PLAYERS_REGISTER_SCHEMA)
    @action(
        detail=False,
        methods=['POST'],
        permission_classes=[IsNotRegisteredPlayer],
    )
    def register(self, request):
        """Register new player."""
        instance = self.get_object()
        serializer = self.get_serializer(instance=instance, data=request.data)
        if serializer.is_valid():
            serializer.save()

            return Response(status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
