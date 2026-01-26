from typing import Any, Dict

import pytest
from django.urls import reverse

from apps.core.models import Contact, Tag
from apps.courts.models import Court, CourtLocation


@pytest.fixture
def location_for_court_data() -> Dict[str, float | str]:
    return {
        'longitude': 12.345,
        'latitude': -54.321,
        'court_name': 'Test court in Thailand',
    }


@pytest.fixture
def cyprus_location_court_data() -> Dict[str, float | str]:
    return {
        'longitude': 34.567,
        'latitude': -12.345,
        'court_name': 'Test court in Cyprus',
    }


@pytest.fixture
def location_for_court_thailand(
    location_for_court_data: Dict[str, Any],
    country_thailand: Any,
    city_in_thailand: Any,
) -> CourtLocation:
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
    cyprus_location_court_data: Dict[str, Any],
    country_cyprus: Any,
    city_in_cyprus: Any,
) -> CourtLocation:
    cyprus_court_data = cyprus_location_court_data.copy()
    another_country = {
        'country': country_cyprus,
        'city': city_in_cyprus,
        'court_name': 'Test court in Cyprus',
    }
    cyprus_court_data.update(another_country)
    return CourtLocation.objects.create(**cyprus_court_data)


@pytest.fixture
def court_data() -> Dict[str, str]:
    return {
        'price_description': '1$/hour',
        'description': 'Test court description',
        'working_hours': 'Test court working hours',
    }


@pytest.fixture
def court_cyprus(
    court_data: Dict[str, Any],
    location_for_court_cyprus: CourtLocation,
) -> Court:
    court_data.update({'location': location_for_court_cyprus})
    return Court.objects.create(**court_data)


@pytest.fixture
def court_thailand(
    court_data: Dict[str, Any],
    location_for_court_thailand: CourtLocation,
) -> Court:
    court_data.update({'location': location_for_court_thailand})
    return Court.objects.create(**court_data)


@pytest.fixture
def tag_data() -> Dict[str, str]:
    return {'name': 'Test tag'}


@pytest.fixture
def tag_obj(tag_data: Dict[str, str]) -> Tag:
    return Tag.objects.create(**tag_data)


@pytest.fixture
def contact_data(court_thailand: Court) -> Dict[str, Any]:
    return {
        'contact_type': 'TEST Phone',
        'contact': '+79999999999',
        'court': court_thailand,
    }


@pytest.fixture
def contact_object(contact_data: Dict[str, Any]) -> Contact:
    return Contact.objects.create(**contact_data)


@pytest.fixture
def court_list_url() -> str:
    return reverse('api:courts-list')


@pytest.fixture
def court_obj_with_tag(
    court_thailand: Court,
    tag_obj: Tag,
) -> Court:
    court_thailand.tag_list.add(tag_obj)
    return court_thailand


@pytest.fixture
def court_api_response_data() -> Dict[str, Any]:
    return {
        'price_description': '1$/hour',
        'description': 'Test court description',
        'contact_list': [
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
