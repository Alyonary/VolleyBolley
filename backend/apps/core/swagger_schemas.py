from drf_yasg import openapi

from apps.core.serializers import CurrencyListSerializer

# faq/ GET
FAQ_GET_SCHEMA = {
    'tags': ['faq'],
    'operation_summary': 'Get FAQ text',
    'operation_description': """
        **Returns:** FAQ text in markdown format.
    """,
    'responses': {
        200: openapi.Response(
            'Success',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'faq': openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description='FAQ text in markdown format',
                    )
                },
            ),
        ),
        404: openapi.Response(
            'Not found',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'faq': openapi.Schema(
                        type=openapi.TYPE_STRING,
                        default='No active FAQ available.',
                    )
                },
            ),
        ),
    },
    'security': [{'Bearer': []}, {'JWT': []}],
}

# /currencies/ GET
CURRENCIES_GET_SCHEMA = {
    'tags': ['currencies'],
    'operation_summary': 'Get all currency types',
    'operation_description': """
        **Returns:** List of all available currency types.
    """,
    'responses': {
        200: openapi.Response('Success', CurrencyListSerializer()),
    },
}
