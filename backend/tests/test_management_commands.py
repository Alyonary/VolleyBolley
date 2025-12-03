import json

import pytest
from django.core.management import call_command

from apps.locations.models import City, Country


def run_load_locations(tmp_path, data):
    file_path = tmp_path / 'locations.json'
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f)
    call_command('load_locations', file=str(file_path))
    return file_path


@pytest.mark.django_db
def test_load_locations_valid(tmp_path, countries_cities_data):
    """
    Test that valid data creates all countries and cities
    as expected.
    """
    run_load_locations(tmp_path, countries_cities_data)
    assert Country.objects.filter(name='Thailand').exists()
    assert Country.objects.filter(name='Cyprus').exists()
    assert City.objects.filter(
        name='Bangkok', country__name='Thailand'
    ).exists()
    assert City.objects.filter(name='Paphos', country__name='Cyprus').exists()


@pytest.mark.django_db
def test_load_locations_city_no_country(tmp_path, countries_cities_data):
    """
    Test that a city with an empty country field is not created.
    """
    data = countries_cities_data.copy()
    data['cities'].append({'name': 'NoCountryCity', 'country': ''})
    run_load_locations(tmp_path, data)
    assert not City.objects.filter(name='NoCountryCity').exists()


@pytest.mark.django_db
def test_load_locations_city_no_name(tmp_path, countries_cities_data):
    """
    Test that a city with an empty name is not created.
    """
    data = countries_cities_data.copy()
    data['cities'].append({'name': '', 'country': 'Thailand'})
    run_load_locations(tmp_path, data)
    assert not City.objects.filter(name='', country__name='Thailand').exists()


@pytest.mark.django_db
def test_load_locations_city_empty_fields(tmp_path, countries_cities_data):
    """
    Test that a city with both name and country empty.
    The city is not created.
    """
    data = countries_cities_data.copy()
    data['cities'].append({'name': '', 'country': ''})
    run_load_locations(tmp_path, data)
    assert not City.objects.filter(name='').exists()


@pytest.mark.django_db
def test_load_locations_duplicate_objects(tmp_path, countries_cities_data):
    """
    Test that running the command twice.
    Using with the same data does not create duplicates.
    """
    run_load_locations(tmp_path, countries_cities_data)
    run_load_locations(tmp_path, countries_cities_data)

    assert Country.objects.filter(name='Thailand').count() == 1
    assert Country.objects.filter(name='Cyprus').count() == 1
    assert (
        City.objects.filter(name='Bangkok', country__name='Thailand').count()
        == 1
    )
    assert (
        City.objects.filter(name='Paphos', country__name='Cyprus').count() == 1
    )
