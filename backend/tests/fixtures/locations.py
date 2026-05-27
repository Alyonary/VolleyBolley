import pytest

from apps.locations.models import City, Country
from django.db.models import QuerySet

import pytest


@pytest.fixture
def countries_cities_data():
    return {
        'countries': [{'name': 'Thailand'}, {'name': 'Cyprus'}],
        'cities': [
            {'name': 'Bangkok', 'country': 'Thailand'},
            {'name': 'Phuket', 'country': 'Thailand'},
            {'name': 'Pattaya', 'country': 'Thailand'},
            {'name': 'Chiang Mai', 'country': 'Thailand'},
            {'name': 'Krabi', 'country': 'Thailand'},
            {'name': 'Nicosia', 'country': 'Cyprus'},
            {'name': 'Limassol', 'country': 'Cyprus'},
            {'name': 'Larnaca', 'country': 'Cyprus'},
            {'name': 'Paphos', 'country': 'Cyprus'},
            {'name': 'Ayia Napa', 'country': 'Cyprus'},
        ],
    }


@pytest.fixture
def countries_cities(countries_cities_data):
    """Create test cities and countries data."""
    countries = {}
    for country_info in countries_cities_data['countries']:
        country = Country.objects.get_or_create(name=country_info['name'])[0]
        countries[country_info['name']] = country

    for city_info in countries_cities_data['cities']:
        country = countries.get(city_info['country'])
        if country:
            City.objects.get_or_create(
                name=city_info['name'], country=country
            )[0]

    return countries


@pytest.fixture
def thailand_bangkok(countries_cities):
    country = countries_cities['Thailand']
    city = City.objects.filter(name='Bangkok')

    return country, city


@pytest.fixture
def countries(countries_cities):
    return Country.objects.all()


@pytest.fixture
def country_thailand():
    return Country.objects.get_or_create(name='Thailand')[0]


@pytest.fixture
def country_cyprus():
    return Country.objects.get_or_create(name='Cyprus')[0]


@pytest.fixture
def city_in_cyprus(country_cyprus):
    return City.objects.get_or_create(name='Limassol', country=country_cyprus)[
        0
    ]


@pytest.fixture
def city_in_thailand(country_thailand):
    return City.objects.get_or_create(
        name='Bangkok', country=country_thailand
    )[0]
