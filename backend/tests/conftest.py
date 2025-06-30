import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.users.models import Location

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user_data():
    return {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'TestPass123',
        'phone_number': '+12345678900',
        'game_skill_level': User.GameSkillLevel.BEGINNER,
    }

@pytest.fixture
def bulk_users_data():
    return [
        {
            'username': 'testuser1',
            'email': 'test1@example.com',
            'password': 'TestPass1',
            'phone_number': '+12345678901',
            'game_skill_level': User.GameSkillLevel.BEGINNER,
        },
        {
            'username': 'testuser2',
            'email': 'test2@example.com',
            'password': 'TestPass2',
            'phone_number': '+12345678902',
            'game_skill_level': User.GameSkillLevel.AMATEUR,
        },
        {
            'username': 'testuser3',
            'email': 'test3@example.com',
            'password': 'TestPass3',
            'phone_number': '+12345678903',
            'game_skill_level': User.GameSkillLevel.ADVANCED,
        },
        {
            'username': 'testuser4',
            'email': 'test4@example.com',
            'password': 'TestPass4',
            'phone_number': '+12345678904',
            'game_skill_level': User.GameSkillLevel.PRO, 
        },
    ]


@pytest.fixture
def user_with_location():
    location = Location.objects.create(country='Russia', city='Moscow')
    user = User.objects.create_user(
        username='locuser',
        email='loc@example.com',
        password='TestPass123',
        phone_number='+79999999999',
        location=location
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
