import pytest
from django.urls import reverse

from apps.core.models import Contact, Tag
from apps.courts.models import Court, CourtLocation
from apps.locations.models import City, Country


@pytest.fixture
def country_for_court_location():
    country = Country.objects.create(name='Thailand')
    return country


@pytest.fixture
def city_for_court_location(country_for_court_location):

    city = City.objects.create(
        name='Pattaya',
        country=country_for_court_location
    )
    return city


@pytest.fixture
def location_for_court_data(
    country_for_court_location,
    city_for_court_location
):
    return {
        'longitude': 12.345,
        'latitude': -54.321,
        'court_name': 'Test court',
        'country': country_for_court_location,
        'city': city_for_court_location
    }


@pytest.fixture
def location_for_court(location_for_court_data):
    return CourtLocation.objects.create(**location_for_court_data)


@pytest.fixture
def court_data(location_for_court):
    return {
        'location': location_for_court,
        'price_description': '1$/hour',
        'description': 'Test court description',
        'working_hours': 'Test court working hours'
    }


@pytest.fixture
def court_obj(court_data):
    return Court.objects.create(**court_data)


@pytest.fixture
def tag_data():
    return {
        'name': 'Test tag'
    }


@pytest.fixture
def tag_obj(tag_data):
    return Tag.objects.create(**tag_data)


@pytest.fixture
def contact_data(court_obj):
    return {
        'contact_type': 'TEST Phone',
        'contact': '+79999999999',
        'court': court_obj
    }


@pytest.fixture
def contact_object(contact_data):
    return Contact.objects.create(**contact_data)


@pytest.fixture
def court_list_url():
    return reverse('api:courts-list')


@pytest.fixture
def court_obj_with_tag(court_obj, tag_obj):
    court_obj.tag_list.add(tag_obj)
    return court_obj


@pytest.fixture
def court_api_response_data():
    return {
        'price_description': '1$/hour',
        'description': 'Test court description',
        'contacts_list': [
            {'contact_type': 'TEST Phone',
             'contact': '+79999999999'}
        ],
        'photo_url': None,
        'tag_list': ['Test tag'],
        'location': {
            'longitude': 12.345,
            'latitude': -54.321,
            'court_name': 'Test court',
            'location_name': 'Test location'
        },
        'court_id': 1}
