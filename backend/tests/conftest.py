import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient


User = get_user_model()

pytest_plugins = [
    "tests.fixtures.courts",
    "tests.fixtures.locations",
    "tests.fixtures.players",
    "tests.fixtures.users",
]

@pytest.fixture
def api_client():
    return APIClient()
