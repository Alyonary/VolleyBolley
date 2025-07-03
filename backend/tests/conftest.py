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
        'first_name': 'NameTestUser',
        'last_name': 'LastnameTestUser',
        'gender': 'M',
        'birth_date': '1991-01-01',
        'email': 'testemail@example.com',
        'password': 'TestPass123',
    }


@pytest.fixture
def bulk_users_data():
    return [
        {
            'first_name': 'NameTestUser',
            'last_name': 'LastnameTestUser',
            'gender': 'M',
            'birth_date': '1991-01-01',
            'email': 'testfirst@example.com',
            'password': 'TestPass123',
        },
        {
            'first_name': 'NameTestUserSecond',
            'last_name': 'LastnameTestUserSecond',
            'gender': 'F',
            'birth_date': '2000-02-02',
            'email': 'testsecond@example.com',
            'password': 'TestPass1234',
        },
        {
            'first_name': 'NameTestUserThird',
            'last_name': 'LastnameTestUserThird',
            'gender': 'O',
            'birth_date': '1993-03-03',
            'email': 'testthird@example.com',
            'password': 'TestPass12345',
        },
        {
            'first_name': 'NameTestUserFourth',
            'last_name': 'LastnameTestUserFourth',
            'gender': 'M',
            'birth_date': '1981-10-11',
            'email': 'testfourth@example.com',
            'password': 'TestPass1235',
        },
    ]


@pytest.fixture
def user_with_location():
    location = Location.objects.create(country='Russia', city='Moscow')
    user = User.objects.create_user(
        email='locationmain@example.com',
        password='TestPass123',
        location=location,
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
