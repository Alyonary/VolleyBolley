from drf_yasg import openapi

from apps.locations.serializers import CountryListSerializer

# locations/countries/ GET
LOCATIONS_COUNTRIES_GET_SCHEMA = {
    'tags': ['locations'],
    'operation_summary': 'Get countries list',
    'operation_description': 'Retrieve all countries with their cities',
    'responses': {200: openapi.Response('Success', CountryListSerializer)},
    'security': [],
}
