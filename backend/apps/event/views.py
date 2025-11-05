from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from apps.core.serializers import EmptyBodySerializer
from apps.event.models import Game, GameInvitation
from apps.event.permissions import IsHostOrReadOnly
from apps.event.serializers import (
    # EventListShortSerializer,
    GameDetailSerializer,
    GameInviteSerializer,
    GameJoinDetailSerializer,
    GameListShortSerializer,
    GameSerializer,
    GameShortSerializer,
)
from apps.event.utils import process_rate_players_request
from apps.players.serializers import PlayerListShortSerializer


class GameViewSet(GenericViewSet):
    """Provides CRUD operations for the Game model."""
    permission_classes = (IsHostOrReadOnly,)
    http_method_names = ['get', 'post', 'delete']

    def get_queryset(self):
        player = getattr(self.request.user, 'player', None)
        if (player is None or
                player.country is None or
                self.action in ('joining_game', 'delete_invitation')):
            return Game.objects.all().select_related(
                    'host', 'court').prefetch_related('players')
        return Game.objects.player_located_games(player).select_related(
                    'host', 'court').prefetch_related('players')

    def get_serializer_class(self, *args, **kwargs):
        if self.action in (
                            'retrieve',
                            'joining_game'):
            return GameDetailSerializer

        if self.action == 'invite_players':
            return GameInviteSerializer

        if self.action in (
                            'my_games',
                            'archive',
                            'invites',
                            'upcoming'):
            return GameShortSerializer
        return GameSerializer

    @swagger_auto_schema(
        tags=['games'],
        operation_summary="Invite list of players to game",
        operation_description="""
        Invite a list of players to the game.

        **Returns:** empty body response.
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['players'],
            properties={
                'players': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_INTEGER),
                    description="List of player IDs",
                    example=[1, 2, 3]
                )
            },
        ),
        responses={
            200: 'Success',
            400: 'Bad request',
            401: 'Unauthorized',
            403: 'Forbidden',
        },
        security=[{'Bearer': []}, {'JWT': []}],
    )
    @action(
        methods=['post'],
        detail=True,
        url_path='invite-players',
    )
    def invite_players(self, request, *args, **kwargs):
        """Creates invitations to the game for players on the list."""
        game_id = self.get_object().id
        host_id = request.user.player.id
        for player_id in request.data['players']:
            serializer = self.get_serializer(
                    data={
                        'host': host_id,
                        'invited': player_id,
                        'game': game_id
                    }
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
        return Response(status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        tags=['games'],
        operation_summary="Get number of active invitations and"
                          " time of next game",
        operation_description="""
        Get number of active invitations and time of next game

        **Returns:** upcoming_game_time, invites.
        """,
        responses={
            200: openapi.Schema(
                title='Success',
                type=openapi.TYPE_OBJECT,
                properties={
                    'upcoming_game_time': openapi.Schema(
                        type=openapi.TYPE_STRING,
                        format='date-time',
                        description='Time in ISO format',
                        example='2025-08-21T15:30:00Z'
                    ),
                    'invites': openapi.Schema(
                        type=openapi.TYPE_INTEGER,
                        description='Number of invitations',
                        example=3,
                    )
                }
            ),
            401: 'Unauthorized',
            403: 'Forbidden',
        },
        security=[{'Bearer': []}, {'JWT': []}],
    )
    @action(
        methods=['get'],
        detail=False,
        url_path='preview'
    )
    def preview(self, request, *args, **kwargs):
        """Returns the time of the next game and the number of invitations."""

        upcoming_game = Game.objects.nearest_game(request.user.player)
        if upcoming_game is not None:
            upcoming_game_time = upcoming_game.start_time
        else:
            upcoming_game_time = None
        invites = GameInvitation.objects.filter(
            invited=request.user.player).values('game').distinct().count()
        return Response(
                data={'upcoming_game_time': upcoming_game_time,
                      'invites': invites}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        tags=['games'],
        operation_summary="Get lists of upcoming games and tournaments"
                          " created by current player.",
        operation_description="""
        Get two lists of the upcoming games and the upcoming tournaments
        created by the current player.
        The player is the host of the events.

        **Returns:** game objects, tournament objects
        """,
        responses={
            200: openapi.Response('Success', GameListShortSerializer),  # TODO: Change for EventListShortSerializer # noqa
            401: 'Unauthorized',
            403: 'Forbidden',
        },
        security=[{'Bearer': []}, {'JWT': []}],
    )
    @action(
        methods=['get'],
        detail=False,
        url_path='my-games'
    )
    def my_games(self, request, *args, **kwargs):
        """Retrieves the list of games created by the user."""

        my_games = Game.objects.my_upcoming_games(request.user.player)
        serializer = self.get_serializer(my_games, many=True)
        wrapped_data = {'games': serializer.data}
        return Response(data=wrapped_data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        tags=['games'],
        operation_summary="Get lists of players archived games"
                          " and tournaments",
        operation_description="""
        Get two lists of the archived games and tournaments
        related to the current player.

        **Returns:** game objects, tournament objects
        """,
        responses={
            200: openapi.Response('Success', GameListShortSerializer),  # TODO: Change for EventListShortSerializer # noqa
            401: 'Unauthorized',
            403: 'Forbidden',
        },
        security=[{'Bearer': []}, {'JWT': []}],
    )
    @action(
        methods=['get'],
        detail=False,
        url_path='archive'
    )
    def archive_games(self, request, *args, **kwargs):
        """Retrieves the list of archived games related to user."""

        archived_games = Game.objects.archive_games(request.user.player)
        serializer = self.get_serializer(archived_games, many=True)
        wrapped_data = {'games': serializer.data}
        return Response(data=wrapped_data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        tags=['games'],
        operation_summary="Get lists of games and tournaments"
                          " to which player has been invited.",
        operation_description="""
        Get two lists of the games and the tournaments
        to which the current player has been invited.
        The player hasn't yet managed the invitations.

        **Returns:** game objects, tournament objects
        """,
        responses={
            200: openapi.Response('Success', GameListShortSerializer),  # TODO: Change for EventListShortSerializer # noqa
            401: 'Unauthorized',
            403: 'Forbidden',
        },
        security=[{'Bearer': []}, {'JWT': []}],
    )
    @action(
        methods=['get'],
        detail=False,
        url_path='invites'
    )
    def invited_games(self, request, *args, **kwargs):
        """Retrieving upcoming games to which the player has been invited."""

        invited_games = Game.objects.invited_games(request.user.player)
        serializer = self.get_serializer(invited_games, many=True)
        wrapped_data = {'games': serializer.data}
        return Response(data=wrapped_data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        tags=['games'],
        operation_summary="Get lists of upcoming games and tournaments"
                          " in which player will participate.",
        operation_description="""
        Get two lists of the upcoming games and the upcoming tournaments
        in which the current player will participate.
        The player has accepted the invitations or is host of the events.

        **Returns:** game objects, tournament objects
        """,
        responses={
            200: openapi.Response('Success', GameListShortSerializer),  # TODO: Change for EventListShortSerializer # noqa
            401: 'Unauthorized',
            403: 'Forbidden',
        },
        security=[{'Bearer': []}, {'JWT': []}],
    )
    @action(
        methods=['get'],
        detail=False,
        url_path='upcoming'
    )
    def upcoming_games(self, request, *args, **kwargs):
        """Retrieving upcoming games that the player participates in."""

        upcoming_games = Game.objects.upcoming_games(request.user.player)
        serializer = self.get_serializer(upcoming_games, many=True)
        wrapped_data = {'games': serializer.data}
        return Response(data=wrapped_data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        tags=['games'],
        operation_summary="Accept invitation to game by player",
        operation_description="""
        The current player accepts an invitation to a game.
        The game id is given as a path-parameter of the request.

        **Returns:** game object.
        """,
        request_body=EmptyBodySerializer,
        manual_parameters=[
            openapi.Parameter(
                'id',
                openapi.IN_PATH,
                description="Game ID",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        responses={
            200: openapi.Response('Success', GameJoinDetailSerializer),  # TODO: Change for EventListShortSerializer # noqa
            401: 'Unauthorized',
            403: 'Forbidden',
        },
        security=[{'Bearer': []}, {'JWT': []}],
    )
    @action(
        methods=['post'],
        detail=True,
        url_path='join-game',
        permission_classes=[IsAuthenticated]
    )
    def joining_game(self, request, *args, **kwargs):
        """Adding a user to the game and removing the invitation."""

        game = self.get_object()
        player = request.user.player
        if game.max_players > game.players.count():
            is_joined = {'is_joined': True}
            game.players.add(player)
            GameInvitation.objects.filter(
                Q(game=game) & Q(invited=player)).delete()
        else:
            is_joined = {'is_joined': False}
        serializer = self.get_serializer(
            game, context={'request': request})
        data = serializer.data.copy()
        data.update(is_joined)
        return Response(data=data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        tags=['games'],
        operation_summary="Reject invitation to game by player",
        operation_description="""
        The current player rejects an invitation to a game.
        The game_id is given as a path-parameter of the request.

        **Returns:** empty body response.
        """,
        responses={
            204: 'No content',  # TODO: Change for EventListShortSerializer # noqa
            400: 'Bad request',
            401: 'Unauthorized',
            403: 'Forbidden',
        },
        security=[{'Bearer': []}, {'JWT': []}],
    )
    @action(
        methods=['delete'],
        detail=True,
        url_path='invites',
        permission_classes=[IsAuthenticated]
    )
    def delete_invitation(self, request, *args, **kwargs):
        game = self.get_object()
        player = request.user.player
        delete_count, dt = GameInvitation.objects.filter(
            Q(game=game) & Q(invited=player)).delete()
        if not delete_count:
            return Response(
                data={'error': _('The invitation does not exist!')},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(
        tags=['games'],
        method='get',
        operation_summary="Get list of players available for rating.",
        operation_description="""
        Get a list of players available for rating.

        **Returns:** player objects.
        """,
        responses={
            200: openapi.Response('Success', PlayerListShortSerializer),  # TODO: Change for EventListShortSerializer # noqa
            401: 'Unauthorized',
            403: 'Forbidden',
        },
        security=[{'Bearer': []}, {'JWT': []}],
    )
    @swagger_auto_schema(
        tags=['games'],
        method='post',
        operation_summary="Rate players by current player.",
        operation_description="""
        The current player rates the other who played in the same events
        as he did.

        **Returns:** empty body response.
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['players'],
            properties={
                'players': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        required=['player_id', 'level_changed'],
                        properties={
                            'player_id': openapi.Schema(
                                type=openapi.TYPE_INTEGER,
                                description='Unique player identifier',
                                example=123
                            ),
                            'level_changed': openapi.Schema(
                                type=openapi.TYPE_STRING,
                                enum=['UP', 'DOWN', 'CONFIRM'],
                                description='Direction of level change',
                                example='UP'
                            )
                        }
                    ),
                    description='List of players with level changes',
                    example=[
                        {'player_id': 1, 'level_changed': 'UP'},
                        {'player_id': 2, 'level_changed': 'DOWN'}
                    ]
                )
            }
        ),
        responses={
            201: 'Success',  # TODO: Change for EventListShortSerializer # noqa
            401: 'Unauthorized',
            403: 'Forbidden',
        },
        security=[{'Bearer': []}, {'JWT': []}],
    )
    @action(
        methods=['get', 'post'],
        detail=True,
        url_path='rate-players',
        permission_classes=[IsHostOrReadOnly]
    )
    def rate_players(self, request, *args, **kwargs):
        """
        Allows a player to rate other players in a game.
        POST: Submits ratings for the specified players.
        GET: Retrieves a list of players available for rating.
        """
        return process_rate_players_request(self, request, *args, **kwargs)
