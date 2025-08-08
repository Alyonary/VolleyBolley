import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()

pytest_plugins = [
    "tests.fixtures.courts",
    "tests.fixtures.locations",
    "tests.fixtures.players",
    "tests.fixtures.users",
    'tests.fixtures.auth',
]


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_api_client_with_not_registered_player(
    api_client, user_generated_after_login
):
    api_client.force_authenticate(user=user_generated_after_login)
    return api_client


@pytest.fixture
def auth_api_client_registered_player(
    api_client, user_with_registered_player
):
    api_client.force_authenticate(user=user_with_registered_player)
    return api_client
