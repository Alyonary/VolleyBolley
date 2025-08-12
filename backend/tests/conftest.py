import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.players.models import Player

User = get_user_model()

pytest_plugins = [
    'tests.fixtures.courts',
    'tests.fixtures.locations',
    'tests.fixtures.players',
    'tests.fixtures.users',
    'tests.fixtures.notifications',
]

@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authenticated_client(api_client):
    """
    Create an authenticated API client.
    Return a tuple of (client, user).
    """

    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='password123'
    )
    Player.objects.create(
        user=user,
    )
    api_client.force_authenticate(user=user)
    return api_client, user