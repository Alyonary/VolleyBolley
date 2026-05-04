from drf_yasg import openapi
from drf_yasg.utils import no_body

from apps.players.serializers import (
    AvatarSerializer,
    PaymentsSerializer,
    PlayerBaseSerializer,
    PlayerListSerializer,
    PlayerRegisterSerializer,
)

# players/register/ POST
PLAYERS_REGISTER_SCHEMA = {
    'tags': ['register'],
    'operation_summary': 'Register new player',
    'operation_description': """
        Register a new player.

        **Notice:**
        - update the basic player instance generated after login
        via social account or via phone number;
        - all fields are required.

        **Returns:** empty body response.
    """,
    'request_body': PlayerRegisterSerializer,
    'responses': {
        200: 'Success',
        400: 'Bad request',
        401: 'Unauthorized',
    },
}

# players/ GET
PLAYER_LIST_SCHEMA = {
    'tags': ['players'],
    'operation_summary': 'List of all players excluding current user',
    'operation_description': """
        **Returns:** a sorted list of all players excluding the current user.
        The favorite players are going first.
    """,
    'responses': {
        200: openapi.Response('Success', PlayerListSerializer(many=True)),
        401: 'Unauthorized',
        403: 'Forbidden',
    },
    'security': [{'Bearer': []}, {'JWT': []}],
}

# players/{id}/ GET
PLAYER_DETAIL_SCHEMA = {
    'tags': ['players'],
    'operation_summary': 'Get info about player',
    'operation_description': (
        '**Returns:** information about the chosen player.'
    ),
    'responses': {
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
                                example='https://example.com',
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
                                                'longitude': openapi.Schema(
                                                    type=openapi.TYPE_NUMBER,
                                                    format=openapi.FORMAT_FLOAT,
                                                    example=37.6173,
                                                ),
                                                'latitude': openapi.Schema(
                                                    type=openapi.TYPE_NUMBER,
                                                    format=openapi.FORMAT_FLOAT,
                                                    example=55.7558,
                                                ),
                                                'court_name': openapi.Schema(
                                                    type=openapi.TYPE_STRING,
                                                    example='Karon Arena',
                                                ),
                                                'location_name': openapi.Schema(  # noqa
                                                    type=openapi.TYPE_STRING,
                                                    example='Russia, Moscow',
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
    'security': [{'Bearer': []}, {'JWT': []}],
}

# players/me/ GET
PLAYERS_ME_SCHEMA = {
    'method': 'get',
    'tags': ['me'],
    'operation_summary': 'Get current player info',
    'operation_description': """
        Get information about the current player

        **Returns:** player object
    """,
    'responses': {
        200: openapi.Response('Success', PlayerBaseSerializer()),
        401: 'Unauthorized',
        403: 'Forbidden',
    },
    'security': [{'Bearer': []}, {'JWT': []}],
}

# players/me/ PATCH
PLAYERS_ME_PATCH_SCHEMA = {
    'method': 'patch',
    'tags': ['me'],
    'operation_summary': 'Update current player info',
    'operation_description': """
        Update the current player object

        **Notice:** All fields are optional.

        **Returns:** empty body response.
    """,
    'request_body': PlayerBaseSerializer(partial=True),
    'responses': {
        200: 'Success',
        400: 'Bad request',
        401: 'Unauthorized',
        403: 'Forbidden',
    },
    'security': [{'Bearer': []}, {'JWT': []}],
}

# players/me/ DELETE
PLAYERS_ME_DELETE_SCHEMA = {
    'method': 'delete',
    'tags': ['me'],
    'operation_summary': 'Delete current player',
    'operation_description': """
        Delete current player by deleting the user associated with
        the player. The player is deleted due to cascade relation.

        **Returns:** empty body response.
    """,
    'responses': {
        204: 'No Content',
        400: 'Bad request',
        401: 'Unauthorized',
        403: 'Forbidden',
    },
    'security': [{'Bearer': []}, {'JWT': []}],
}

# players/me/avatar/ PUT
AVATAR_ME_PUT_SCHEMA = {
    'method': 'put',
    'tags': ['avatar'],
    'operation_summary': 'Update or delete avatar',
    'operation_description': """
        Update or delete avatar

        To delete avatar set its value to 'null'.
    """,
    'request_body': openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'avatar': openapi.Schema(
                type=openapi.TYPE_STRING,
                description='Base64 encoded image',
            ),
        },
        required=['avatar'],
    ),
    'responses': {
        200: openapi.Response('Success', AvatarSerializer),
        400: 'Bad request',
        401: 'Unauthorized',
        403: 'Forbidden',
    },
    'security': [{'Bearer': []}, {'JWT': []}],
}

# players/me/payments/ GET
PAYMENTS_ME_GET_SCHEMA = {
    'method': 'get',
    'tags': ['payments'],
    'operation_summary': 'Get payment data of player',
    'operation_description': """
        Get payment data of player

        **Returns:** list of players payments.
    """,
    'responses': {
        200: openapi.Response('Success', PaymentsSerializer()),
        401: 'Unauthorized',
        403: 'Forbidden',
    },
    'security': [{'Bearer': []}, {'JWT': []}],
}

# players/me/payments/ PUT
PAYMENTS_ME_PUT_SCHEMA = {
    'method': 'put',
    'tags': ['payments'],
    'operation_summary': 'Update payment data of player',
    'operation_description': """
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
    'request_body': PaymentsSerializer,
    'responses': {
        200: 'Success',
        400: 'Bad request',
        401: 'Unauthorized',
        403: 'Forbidden',
    },
    'security': [{'Bearer': []}, {'JWT': []}],
}

# players/{id}/favorite/ POST
FAVORITE_POST_SCHEMA = {
    'method': 'post',
    'tags': ['favorite'],
    'operation_summary': 'Add player to favorite list',
    'operation_description': """
        Add a player to a favorite list

        **Returns:** empty body response.
    """,
    'request_body': no_body,
    'responses': {
        201: 'Success',
        400: 'Bad request',
        401: 'Unauthorized',
        403: 'Forbidden',
    },
    'security': [{'Bearer': []}, {'JWT': []}],
}

# players/{id}/favorite/ DELETE
FAVORITE_DELETE_SCHEMA = {
    'method': 'delete',
    'tags': ['favorite'],
    'operation_summary': 'Delete player from favorite list',
    'operation_description': """
        Add a player to a favorite list

        **Returns:** empty body response.
    """,
    'responses': {
        204: 'No Content',
        400: 'Bad request',
        401: 'Unauthorized',
        403: 'Forbidden',
    },
    'security': [{'Bearer': []}, {'JWT': []}],
}
