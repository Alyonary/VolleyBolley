import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from apps.core.models import Contact, Tag
from apps.courts.models import Court, CourtLocation
from apps.locations.models import City, Country
from apps.players.models import Player, PlayerLocation


User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user_data():
    return {
        'first_name': 'TestName',
        'last_name': 'TestLastName',
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'TestPass123',
        'phone_number': '+12345678900',
    }


@pytest.fixture
def bulk_users_data():
    return [
        {
            'username': 'testuser1',
            'email': 'test1@example.com',
            'password': 'TestPass1',
            'phone_number': '+12345678901',
        },
        {
            'username': 'testuser2',
            'email': 'test2@example.com',
            'password': 'TestPass2',
            'phone_number': '+12345678902',
        },
        {
            'username': 'testuser3',
            'email': 'test3@example.com',
            'password': 'TestPass3',
            'phone_number': '+12345678903',
        },
        {
            'username': 'testuser4',
            'email': 'test4@example.com',
            'password': 'TestPass4',
            'phone_number': '+12345678904',
        },
    ]


@pytest.fixture
def user_with_location():
    user = User.objects.create_user(
        username='locuser',
        email='loc@example.com',
        password='TestPass123',
        phone_number='+79999999999',
    )
    return user


@pytest.fixture
def create_user(user_data):
    return User.objects.create_user(**user_data)


@pytest.fixture
def active_user(user_data):
    user = User.objects.create_user(**user_data)
    user.is_active = True
    user.save()
    return user


@pytest.fixture
def bulk_create_users(bulk_users_data):
    return [User.objects.create(**user) for user in bulk_users_data]


@pytest.fixture
def sample_location():
    return PlayerLocation.objects.create(
        country='Russia',
        city='Moscow'
    )


@pytest.fixture
def player_data(active_user, sample_location):
    return {
        'user': active_user,
        'gender': 'MALE',
        'level': 'LIGHT',
        'location': sample_location
    }


@pytest.fixture
def player_male_light(player_data):
    return Player.objects.create(**player_data)


@pytest.fixture
def countries_cities():
    '''Create test cities and countries data.'''
    thailand = Country.objects.create(name='Thailand')
    cyprus = Country.objects.create(name='Cyprus')
    
    City.objects.create(name='Bangkok', country=thailand)
    City.objects.create(name='Pattaya', country=thailand)
    City.objects.create(name='Limassol', country=cyprus)
    City.objects.create(name='Nicosia', country=cyprus)
    
    return {'thailand': thailand, 'cyprus': cyprus}

@pytest.fixture
def countries_cities_data(countries_cities):
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


def location_for_court_data():
    return {
        'longitude': 12.345,
        'latitude': -54.321,
        'court_name': 'Test court',
        'location_name': 'Test location'
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
