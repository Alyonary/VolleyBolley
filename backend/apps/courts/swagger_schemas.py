from drf_yasg import openapi

from apps.courts.serializers import CourtSerializer

COURTS_LIST_SCHEMA = {
    'tags': ['courts'],
    'operation_summary': 'List of filtered courts',
    'operation_description': """
        **Returns:** a list of courts filtered depending on players location.
    """,
    'responses': {
        200: openapi.Response('Success', CourtSerializer(many=True)),
        401: 'Unauthorized',
        403: 'Forbidden',
    },
    'security': [{'Bearer': []}, {'JWT': []}],
}
