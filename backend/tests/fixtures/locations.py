import pytest

from apps.locations.models import City, Country


@pytest.fixture
def countries_cities_data():
    return {
        'countries': [
            {
                'name': 'Thailand'
            },
            {
                'name': 'Cyprus'
            }
        ],
        'cities': [
            {
                'name': 'Bangkok',
                'country': 'Thailand'
            },
            {
                'name': 'Paphos',
                'country': 'Cyprus'
            }
        ]
    }

@pytest.fixture
def countries_cities(countries_cities_data):
    '''Create test cities and countries data.'''

    countries = {}
    for country_info in countries_cities_data['countries']:
        country = Country.objects.create(name=country_info['name'])
        countries[country_info['name']] = country

    for city_info in countries_cities_data['cities']:
        country = countries.get(city_info['country'])
        if country:
            City.objects.create(name=city_info['name'], country=country)

    return countries