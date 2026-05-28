from typing import Tuple

import pytest
from rest_framework.test import APIClient

from apps.locations.models import City, Country
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


@pytest.fixture
def authenticated_client_thailand_player(
    api_client: APIClient, country_thailand: Country, city_in_thailand: City
) -> Tuple[APIClient, User]:
    """
    Create an authenticated API client with a player from Thailand.
    Return a tuple of (client, user).
    """
    user: User = User.objects.create_user(
        username='thaiuser',
        password='password123',
    )
    player: Player = Player.objects.create(
        user=user,
        is_registered=True,
        country=country_thailand,
        city=city_in_thailand,
    )
    api_client.force_authenticate(user=user)
    return api_client, player


@pytest.fixture
def authenticated_client_сyprus_player(
    api_client: APIClient, country_cyprus: Country, city_in_cyprus: City
) -> Tuple[APIClient, User]:
    """
    Create an authenticated API client with a player from Cyprus.
    Return a tuple of (client, user).
    """
    user: User = User.objects.create_user(
        username='cyprususer',
        password='password123',
    )
    player: Player = Player.objects.create(
        user=user,
        is_registered=True,
        country=country_cyprus,
        city=city_in_cyprus,
    )
    api_client.force_authenticate(user=user)
    return api_client, player
