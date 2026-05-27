import pytest
from typing import Tuple
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from rest_framework.test import APIClient
from apps.players.models import Player
from apps.users.models import User

pytest_plugins: list[str] = [
    'tests.fixtures.auth',
    'tests.fixtures.core',
    'tests.fixtures.courts',
    'tests.fixtures.games',
    'tests.fixtures.locations',
    'tests.fixtures.notifications',
    'tests.fixtures.players',
    'tests.fixtures.push_service',
    'tests.fixtures.tourneys',
    'tests.fixtures.users',
]


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def auth_api_client_with_not_registered_player(
    api_client: APIClient, user_generated_after_login: User
) -> APIClient:
    api_client.force_authenticate(user=user_generated_after_login)
    return api_client


@pytest.fixture
def auth_api_client_registered_player(
    api_client: APIClient, user_with_registered_player: User
) -> APIClient:
    api_client.force_authenticate(user=user_with_registered_player)
    return api_client


@pytest.fixture
def authenticated_client(api_client: APIClient) -> Tuple[APIClient, User]:
    """
    Create an authenticated API client.
    Return a tuple of (client, user).
    """
    user: User = User.objects.create_user(
        username='testuser', email='test@example.com', password='password123'
    )
    Player.objects.create(user=user, is_registered=True)
    api_client.force_authenticate(user=user)
    return api_client, user
