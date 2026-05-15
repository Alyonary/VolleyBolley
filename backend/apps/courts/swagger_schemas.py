from drf_yasg import openapi

from apps.courts.serializers import (
    CourtSerializer,
    CourtWithEventsSerializer,
)

COURTS_LIST_SCHEMA = {
    'operation_description': (
        'Get a list of courts with geographic filtering.'
    ),
    'manual_parameters': [
        openapi.Parameter(
            'active_events',
            openapi.IN_QUERY,
            description='True — return only courts that have events',
            type=openapi.TYPE_BOOLEAN,
        ),
    ],
    'responses': {200: CourtSerializer(many=True)},
}


COURTS_RETRIEVE_SCHEMA = {
    'operation_description': (
        'Get detailed information about a specific court.'
    ),
    'manual_parameters': [
        openapi.Parameter(
            'events_detail',
            openapi.IN_QUERY,
            description=(
                "True — include 'games' and 'tourney' keys in the response"
            ),
            type=openapi.TYPE_BOOLEAN,
        ),
    ],
    'responses': {
        200: openapi.Response(
            description=(
                'Successful response. Structure depends on events_detail flag.'
            ),
            schema=CourtWithEventsSerializer,
        )
    },
}
