from django.contrib.auth.models import AnonymousUser
from django.db.models import Exists, OuterRef, Prefetch
from django.shortcuts import get_object_or_404
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from apps.core.permissions import IsNotRegisteredPlayer, IsRegisteredPlayer
from apps.core.serializers import EmptyBodySerializer
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

    @swagger_auto_schema(
        tags=['players'],
        operation_summary='List of all players excluding current user',
        operation_description="""
        **Returns:** a sorted list of all players excluding the current user.
        The favorite players are going first.
        """,
        responses={
            200: openapi.Response('Success', PlayerListSerializer(many=True)),
            401: 'Unauthorized',
            403: 'Forbidden',
        },
        security=[{'Bearer': []}, {'JWT': []}],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['players'],
        operation_summary='Get info about player',
        operation_description="""
        **Returns:** information about the chosen player.
        """,
        responses={
            200: openapi.Response(
                description='Player details retrieved successfully',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'player': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'player_id': openapi.Schema(
                                    type=openapi.TYPE_INTEGER, example=1
                                ),
                                'first_name': openapi.Schema(
                                    type=openapi.TYPE_STRING, example='Ivan'
                                ),
                                'last_name': openapi.Schema(
                                    type=openapi.TYPE_STRING, example='Petrov'
                                ),
                                'avatar': openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    format=openapi.FORMAT_URI,
                                    example='https://storage.example.com/'
                                    'avatars/1.jpg',
                                ),
                                'is_favorite': openapi.Schema(
                                    type=openapi.TYPE_BOOLEAN, example=False
                                ),
                                'level': openapi.Schema(
                                    type=openapi.TYPE_STRING, example='PRO'
                                ),
                                'latest_activity': openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    items=openapi.Schema(
                                        type=openapi.TYPE_OBJECT,
                                        properties={
                                            'event_timestamp': openapi.Schema(
                                                type=openapi.TYPE_STRING,
                                                format=openapi.FORMAT_DATETIME,
                                                example='2025-07-12T14:23:45Z',
                                            ),
                                            'court_location': openapi.Schema(
                                                type=openapi.TYPE_OBJECT,
                                                properties={
                                                    'longitude': openapi.Schema(  # noqa
                                                        type=openapi.TYPE_NUMBER,  # noqa
                                                        format=openapi.FORMAT_FLOAT,  # noqa
                                                        example=37.6173,
                                                    ),
                                                    'latitude': openapi.Schema(
                                                        type=openapi.TYPE_NUMBER,  # noqa
                                                        format=openapi.FORMAT_FLOAT,  # noqa
                                                        example=55.7558,
                                                    ),
                                                    'court_name': openapi.Schema(  # noqa
                                                        type=openapi.TYPE_STRING,  # noqa
                                                        example='Karon Arena',
                                                    ),
                                                    'location_name': openapi.Schema(  # noqa
                                                        type=openapi.TYPE_STRING,  # noqa
                                                        example='Russia, Moscow',  # noqa
                                                    ),
                                                },
                                            ),
                                        },
                                    ),
                                ),
                            },
                        )
                    },
                ),
            ),
            401: 'Unauthorized',
            403: 'Forbidden',
        },
        security=[{'Bearer': []}, {'JWT': []}],
    )
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        serializer = PlayerKeyDetailSerializer(instance={'player': instance})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        tags=['me'],
        method='get',
        operation_summary='Get current player info',
        operation_description="""
        Get information about the current player

        **Returns:** player object
        """,
        responses={
            200: openapi.Response('Success', PlayerBaseSerializer()),
            401: 'Unauthorized',
            403: 'Forbidden',
        },
        security=[{'Bearer': []}, {'JWT': []}],
    )
    @swagger_auto_schema(
        tags=['me'],
        method='patch',
        operation_summary='Update current player info',
        operation_description="""
        Update the current player object

        **Notice:** All fields are optional.

        **Returns:** empty body response.
        """,
        request_body=PlayerBaseSerializer(partial=True),
        responses={
            200: 'Success',
            400: 'Bad request',
            401: 'Unauthorized',
            403: 'Forbidden',
        },
        security=[{'Bearer': []}, {'JWT': []}],
    )
    @swagger_auto_schema(
        tags=['me'],
        method='delete',
        operation_summary='Delete current player',
        operation_description="""
        Delete current player by deleting the user associated with
        the player. The player is deleted due to cascade relation.

        **Returns:** empty body response.
        """,
        responses={
            204: 'No Content',
            400: 'Bad request',
            401: 'Unauthorized',
            403: 'Forbidden',
        },
        security=[{'Bearer': []}, {'JWT': []}],
    )
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

    @swagger_auto_schema(
        tags=['avatar'],
        method='put',
        operation_summary='Update or delete avatar',
        operation_description="""
        Update or delete avatar

        To delete avatar set its value to 'null'.
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'avatar': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Base64 encoded image',
                ),
            },
            required=['avatar'],
        ),
        responses={
            200: openapi.Response('Success', AvatarSerializer),
            400: 'Bad request',
            401: 'Unauthorized',
            403: 'Forbidden',
        },
        security=[{'Bearer': []}, {'JWT': []}],
    )
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

            return Response(status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        tags=['payments'],
        method='get',
        operation_summary='Get payment data of player',
        operation_description="""
        Get payment data of player

        **Returns:** list of players payments.
        """,
        responses={
            200: openapi.Response('Success', PaymentsSerializer()),
            401: 'Unauthorized',
            403: 'Forbidden',
        },
        security=[{'Bearer': []}, {'JWT': []}],
    )
    @swagger_auto_schema(
        tags=['payments'],
        method='put',
        operation_summary='Update payment data of player',
        operation_description="""
        Update players payment data.

        **Notice:**
        - list of payments data should be provided;
        - only one of the players payments must have the attribute
        'is_preferred=True', the other payment with the attribute
        'is_preferred=True' should be rewritten with the attribute
        'is_preferred=False' during the same request;
        - it is better to rewrite the whole collection of players payments
        at once;
        - all fields of a payment are required.

        **Returns:** empty body response.
        """,
        request_body=PaymentsSerializer,
        responses={
            200: 'Success',
            400: 'Bad request',
            401: 'Unauthorized',
            403: 'Forbidden',
        },
        security=[{'Bearer': []}, {'JWT': []}],
    )
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

    @swagger_auto_schema(
        tags=['favorite'],
        method='post',
        operation_summary='Add player to favorite list',
        operation_description="""
        Add a player to a favorite list

        **Returns:** empty body response.
        """,
        request_body=EmptyBodySerializer,
        responses={
            201: 'Success',
            400: 'Bad request',
            401: 'Unauthorized',
            403: 'Forbidden',
        },
        security=[{'Bearer': []}, {'JWT': []}],
    )
    @swagger_auto_schema(
        tags=['favorite'],
        method='delete',
        operation_summary='Delete player from favorite list',
        operation_description="""
        Add a player to a favorite list

        **Returns:** empty body response.
        """,
        responses={
            204: 'No Content',
            400: 'Bad request',
            401: 'Unauthorized',
            403: 'Forbidden',
        },
        security=[{'Bearer': []}, {'JWT': []}],
    )
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

    @swagger_auto_schema(
        tags=['register'],
        operation_summary='Register new player',
        operation_description="""
        Register a new player.

        **Notice:**
        - update the basic player instance generated after login
        via social account or via phone number;
        - all fields are required.

        **Returns:** empty body response.
        """,
        request_body=PlayerRegisterSerializer,
        responses={
            200: 'Success',
            400: 'Bad request',
            401: 'Unauthorized',
        },
    )
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
