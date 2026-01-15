import pytest
from django.urls import reverse

from apps.core.models import Contact, Tag
from apps.courts.models import Court, CourtLocation


@pytest.fixture
def location_for_court_data():
    return {
        'longitude': 12.345,
        'latitude': -54.321,
        'court_name': 'Test court in Thailand',
    }


@pytest.fixture
def location_for_court_thailand(
    location_for_court_data, country_thailand, city_in_thailand
):
    thailand_court_data = location_for_court_data.copy()
    thailand_court_data.update(
        {
            'court_name': 'Test court in Thailand',
            'country': country_thailand,
            'city': city_in_thailand,
        }
    )
    return CourtLocation.objects.create(**thailand_court_data)


@pytest.fixture
def location_for_court_cyprus(
    location_for_court_data, country_cyprus, city_in_cyprus
):
    cyprus_court_data = location_for_court_data.copy()
    another_country = {
        'country': country_cyprus,
        'city': city_in_cyprus,
        'court_name': 'Test court in Cyprus',
    }
    cyprus_court_data.update(another_country)
    return CourtLocation.objects.create(**cyprus_court_data)


@pytest.fixture
def court_data():
    return {
        'price_description': '1$/hour',
        'description': 'Test court description',
        'working_hours': 'Test court working hours',
    }


@pytest.fixture
def court_cyprus(court_data, location_for_court_cyprus):
    court_data.update({'location': location_for_court_cyprus})
    return Court.objects.create(**court_data)


@pytest.fixture
def court_thailand(court_data, location_for_court_thailand):
    court_data.update({'location': location_for_court_thailand})
    return Court.objects.create(**court_data)


@pytest.fixture
def tag_data():
    return {'name': 'Test tag'}


@pytest.fixture
def tag_obj(tag_data):
    return Tag.objects.create(**tag_data)


@pytest.fixture
def contact_data(court_thailand):
    return {
        'contact_type': 'TEST Phone',
        'contact': '+79999999999',
        'court': court_thailand,
    }


@pytest.fixture
def contact_object(contact_data):
    return Contact.objects.create(**contact_data)


@pytest.fixture
def court_list_url():
    return reverse('api:courts-list')


@pytest.fixture
def court_obj_with_tag(court_thailand, tag_obj):
    court_thailand.tag_list.add(tag_obj)
    return court_thailand


@pytest.fixture
def court_api_response_data():
    return {
        'price_description': '1$/hour',
        'description': 'Test court description',
        'contacts_list': [
            {'contact_type': 'TEST Phone', 'contact': '+79999999999'}
        ],
        'photo_url': None,
        'tags': ['Test tag'],
        'location': {
            'longitude': 12.345,
            'latitude': -54.321,
            'court_name': 'Test court',
            'location_name': 'Test location',
        },
        'court_id': 1,
    }
