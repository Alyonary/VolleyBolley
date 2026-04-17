from drf_yasg import openapi
from drf_yasg.utils import no_body

from apps.event.serializers import (
    GameDetailSerializer,
    GameJoinDetailSerializer,
    GameListShortSerializer,
    GameSerializer,
)
from apps.players.serializers import PlayerListShortSerializer

# /games/{id}/invite-players/ POST
GAMES_INVITE_PLAYERS_POST_SCHEMA = dict(
    tags=['games'],
    operation_summary='Invite list of players to game',
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
                description='List of player IDs',
                example=[1, 2, 3],
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

# /games/preview/ GET
GAMES_PREVIEW_GET_SCHEMA = dict(
    tags=['games'],
    operation_summary='Get number of active invitations and time of next game',
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
                    example='2025-08-21T15:30:00Z',
                ),
                'invites': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description='Number of invitations',
                    example=3,
                ),
            },
        ),
        401: 'Unauthorized',
        403: 'Forbidden',
    },
    security=[{'Bearer': []}, {'JWT': []}],
)

# /games/my-games/ GET
GAMES_MY_GAMES_GET_SCHEMA = dict(
    tags=['games'],
    operation_summary=(
        'Get lists of upcoming games and tournaments created by current player'
    ),
    operation_description="""
    Get two lists of the upcoming games and the upcoming tournaments
    created by the current player.
    The player is the host of the events.

    **Returns:** game objects, tournament objects
    """,
    responses={
        200: openapi.Response('Success', GameListShortSerializer),
        401: 'Unauthorized',
        403: 'Forbidden',
    },
    security=[{'Bearer': []}, {'JWT': []}],
)

# /games/archive/ GET
GAMES_ARCHIVE_GET_SCHEMA = dict(
    tags=['games'],
    operation_summary='Get lists of players archived games and tournaments',
    operation_description="""
    Get two lists of the archived games and tournaments
    related to the current player.

    **Returns:** game objects, tournament objects
    """,
    responses={
        200: openapi.Response('Success', GameListShortSerializer),
        401: 'Unauthorized',
        403: 'Forbidden',
    },
    security=[{'Bearer': []}, {'JWT': []}],
)

# /games/invites/ GET
GAMES_INVITES_GET_SCHEMA = dict(
    tags=['games'],
    operation_summary=(
        'Get lists of games and tournaments to which player has been invited'
    ),
    operation_description="""
    Get two lists of the games and the tournaments
    to which the current player has been invited.
    The player hasn't yet managed the invitations.

    **Returns:** game objects, tournament objects
    """,
    responses={
        200: openapi.Response('Success', GameListShortSerializer),
        401: 'Unauthorized',
        403: 'Forbidden',
    },
    security=[{'Bearer': []}, {'JWT': []}],
)

# /games/upcoming/ GET
GAMES_UPCOMING_GET_SCHEMA = dict(
    tags=['games'],
    operation_summary=(
        'Get lists of upcoming games and tournaments'
        'in which player will participate'
    ),
    operation_description="""
    Get two lists of the upcoming games and the upcoming tournaments
    in which the current player will participate.
    The player has accepted the invitations or is host of the events.

    **Returns:** game objects, tournament objects
    """,
    responses={
        200: openapi.Response('Success', GameListShortSerializer),
        401: 'Unauthorized',
        403: 'Forbidden',
    },
    security=[{'Bearer': []}, {'JWT': []}],
)

# /games/{id}/join-game/ POST
GAMES_JOIN_GAME_POST_SCHEMA = dict(
    tags=['games'],
    operation_summary='Accept invitation to game by player',
    operation_description="""
    The current player accepts an invitation to a game.
    The game id is given as a path-parameter of the request.

    **Returns:** game object.
    """,
    request_body=no_body,
    manual_parameters=[
        openapi.Parameter(
            'id',
            openapi.IN_PATH,
            description='Game ID',
            type=openapi.TYPE_INTEGER,
            required=True,
        )
    ],
    responses={
        200: openapi.Response('Success', GameJoinDetailSerializer),
        401: 'Unauthorized',
        403: 'Forbidden',
    },
    security=[{'Bearer': []}, {'JWT': []}],
)

# /games/{id}/invites/ DELETE
GAMES_INVITES_DELETE_SCHEMA = dict(
    tags=['games'],
    operation_summary='Reject invitation to game by player',
    operation_description="""
    The current player rejects an invitation to a game.
    The game_id is given as a path-parameter of the request.

    **Returns:** empty body response.
    """,
    responses={
        204: 'No content',
        400: 'Bad request',
        401: 'Unauthorized',
        403: 'Forbidden',
    },
    security=[{'Bearer': []}, {'JWT': []}],
)

# /games/{id}/rate-players/ GET
GAMES_RATE_PLAYERS_GET_SCHEMA = dict(
    tags=['games'],
    method='get',
    operation_summary='Get list of players available for rating',
    operation_description="""
    Get a list of players available for rating.

    **Returns:** player objects.
    """,
    responses={
        200: openapi.Response('Success', PlayerListShortSerializer),
        401: 'Unauthorized',
        403: 'Forbidden',
    },
    security=[{'Bearer': []}, {'JWT': []}],
)

# /games/{id}/rate-players/ POST
GAMES_RATE_PLAYERS_POST_SCHEMA = dict(
    tags=['games'],
    method='post',
    operation_summary='Rate players by current player',
    operation_description="""
    The current player rates the other who played in the same event
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
                            example=123,
                        ),
                        'level_changed': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            enum=['UP', 'DOWN', 'CONFIRM'],
                            description='Direction of level change',
                            example='UP',
                        ),
                    },
                ),
                description='List of players with level changes',
                example=[
                    {'player_id': 1, 'level_changed': 'UP'},
                    {'player_id': 2, 'level_changed': 'DOWN'},
                ],
            )
        },
    ),
    responses={
        201: 'Success',
        401: 'Unauthorized',
        403: 'Forbidden',
    },
    security=[{'Bearer': []}, {'JWT': []}],
)

# /games/ POST
GAMES_POST_SCHEMA = dict(
    tags=['games'],
    operation_summary='Create game',
    operation_description="""
    Create a new game. The current player becomes the host of the game.

    **Returns:** game object.
    """,
    request_body=GameSerializer,
    responses={
        201: openapi.Response('Success', GameSerializer),
        400: 'Bad request',
        401: 'Unauthorized',
        403: 'Forbidden',
    },
    security=[{'Bearer': []}, {'JWT': []}],
)

# /games/{id}/ GET
GAMES_DETAIL_GET_SCHEMA = dict(
    tags=['games'],
    operation_summary='Get game info',
    operation_description="""
    Get information about a game.

    **Returns:** game object.
    """,
    responses={
        200: openapi.Response('Success', GameDetailSerializer),
        401: 'Unauthorized',
        403: 'Forbidden',
    },
    security=[{'Bearer': []}, {'JWT': []}],
)

# /games/{id}/ DELETE
GAMES_DETAIL_DELETE_SCHEMA = dict(
    tags=['games'],
    operation_summary='Delete game',
    operation_description="""
    Delete a game by the current player.
    The game could be deleted only by its host.

    **Returns:** empty body response.
    """,
    responses={
        204: 'No content',
        401: 'Unauthorized',
        403: 'Forbidden',
    },
    security=[{'Bearer': []}, {'JWT': []}],
)
