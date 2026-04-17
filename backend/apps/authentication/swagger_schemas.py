from drf_yasg import openapi

from apps.authentication.serializers import (
    LoginSerializer,
)

# /auth/logout/ POST
AUTH_LOGOUT_POST_SCHEMA = dict(
    tags=['auth'],
    operation_summary='Logout by blacklisting refresh token',
    operation_description="""
    Logout by blacklisting refresh token

    **Returns:**
    - no response body if logout is successful.
    """,
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'refresh_token': openapi.Schema(
                type=openapi.TYPE_STRING,
                description='Refresh token to blacklist',
            ),
        },
        required=['refresh_token'],
    ),
    responses={
        205: 'Successful logout',
        400: 'Bad request',
        401: 'Unauthorized',
    },
    security=[{'Bearer': []}, {'JWT': []}],
)

# /auth/google/login  POST
AUTH_GOOGLE_POST_SCHEMA = dict(
    tags=['auth'],
    operation_summary='Authenticate via Google (id_token)',
    operation_description="""
    Authenticate user in the app via 'id_token' or 'access_token'
    received from Google.

    **Returns:**
    - `access_token`: JWT token for API access
    - `refresh_token`: Token for refreshing access_token
    - `player`: Player data associated with the user
    """,
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'access_token': openapi.Schema(
                type=openapi.TYPE_STRING, description='Google access token'
            ),
            'id_token': openapi.Schema(
                type=openapi.TYPE_STRING, description='Google ID token'
            ),
        },
        anyOf=[{'required': ['access_token']}, {'required': ['id_token']}],
        description="'id_token' or 'access_token' must be provided.",
    ),
    responses={
        200: openapi.Response(
            'Successful authentication',
            LoginSerializer,
        ),
        400: 'Bad request',
    },
    security=[],
)

# /auth/google/login GET
AUTH_GOOGLE_GET_SCHEMA = dict(
    operation_summary='Start Google OAuth authentication',
    operation_description="""
    Initiates the OAuth 2.0 authentication process with Google.

    ## Flow:
    1. User accesses this URL
    2. Redirects to Google authorization page
    3. User authenticates with Google
    4. Google redirects to callback URL with code
    5. Server exchanges code for access token
    """,
    tags=['auth'],
    responses={
        302: openapi.Response(
            description='Redirect to Google OAuth',
            headers={
                'Location': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='URL for Google authorization',
                    example=(
                        'https://accounts.google.com/o/oauth2/auth?'
                        'response_type=code&client_id=...'
                    ),
                )
            },
        ),
    },
    security=[],
)

# /auth/phone-number/login POST
AUTH_PHONE_POST_SCHEMA = dict(
    tags=['auth'],
    operation_summary='Authenticate via phone number (firebase id_token)',
    operation_description="""
    Authenticate user in the app via 'id_token' received from the Firebase
    application during the authentication process via phone number.

    **Returns:**
    - `access_token`: JWT token for API access
    - `refresh_token`: Token for refreshing access_token
    - `player`: Player data associated with the user
    """,
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'id_token': openapi.Schema(
                type=openapi.TYPE_STRING, description='Firebase ID token'
            ),
        },
        required=['id_token'],
    ),
    responses={
        200: openapi.Response(
            'Successful authentication',
            LoginSerializer,
        ),
        400: 'Bad request',
    },
    security=[],
)

# /auth/facebook/login POST
AUTH_FACEBOOK_POST_SCHEMA = dict(
    tags=['auth'],
    operation_summary='Authenticate via Facebook (firebase id_token)',
    operation_description="""
    Authenticate user in the app via 'id_token' received from the Firebase
    application during the authentication process via Facebook.

    **Returns:**
    - `access_token`: JWT token for API access
    - `refresh_token`: Token for refreshing access_token
    - `player`: Player data associated with the user
    """,
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'id_token': openapi.Schema(
                type=openapi.TYPE_STRING, description='Firebase ID token'
            ),
        },
        required=['id_token'],
    ),
    responses={
        200: openapi.Response(
            'Successful authentication',
            LoginSerializer,
        ),
        400: 'Bad request',
    },
    security=[],
)

# /auth/google/login/v2 POST
AUTH_GOOGLE_V2_POST_SCHEMA = dict(
    tags=['auth'],
    operation_summary='Authenticate via Google (firebase id_token)',
    operation_description="""
    Authenticate user in the app via 'id_token' received from the Firebase
    application during the authentication process via Google.

    **Returns:**
    - `access_token`: JWT token for API access
    - `refresh_token`: Token for refreshing access_token
    - `player`: Player data associated with the user
    """,
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'id_token': openapi.Schema(
                type=openapi.TYPE_STRING, description='Firebase ID token'
            ),
        },
        required=['id_token'],
    ),
    responses={
        200: openapi.Response(
            'Successful authentication',
            LoginSerializer,
        ),
        400: 'Bad request',
    },
    security=[],
)

# /auth/token/refresh/ POST
AUTH_TOKEN_REFRESH_POST_SCHEMA = dict(
    operation_summary='Refresh access_token',
    operation_description="""
    Refreshes access_token using refresh_token.

    **Important:** refresh_token does NOT change during refresh.

    **Returns:**
    - `access_token`: New access token
    """,
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['refresh_token'],
        properties={
            'refresh_token': openapi.Schema(
                type=openapi.TYPE_STRING,
                description='Refresh token generated previously.',
                example='eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1Ni...',
            ),
        },
    ),
    responses={
        200: openapi.Response(
            description='Access token successfully refreshed',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'access_token': openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description='New access token',
                    ),
                },
            ),
            examples={
                'application/json': {
                    'access_token': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1Ni...'
                }
            },
        ),
        400: 'Bad request',
    },
    security=[],
)

# /auth/token/verify/ POST
AUTH_TOKEN_VERIFY_POST_SCHEMA = dict(
    operation_summary='Verify access_token',
    operation_description="""
    Verifies access_token validity.

    **Returns:**
    - Empty object with 200 status on successful verification
    """,
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['access_token'],
        properties={
            'access_token': openapi.Schema(
                type=openapi.TYPE_STRING,
                description='Access token to verify validity',
                example='eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
            ),
        },
    ),
    responses={
        200: openapi.Response(
            description='Token is valid',
            schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={}),
            examples={'application/json': {}},
        ),
        400: 'Bad request',
    },
    security=[],
)
