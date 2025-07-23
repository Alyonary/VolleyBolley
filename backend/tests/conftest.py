import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.players.models import Player, PlayerLocation
from apps.locations.models import City, Country

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
