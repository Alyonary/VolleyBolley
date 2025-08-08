import pytest
from rest_framework_simplejwt.tokens import RefreshToken


@pytest.fixture
def google_response():
    return {
        'email': 'test@example.com',
        'sub': '1234567890',
        'given_name': 'Test',
        'family_name': 'User',
        'name': 'Test User'
    }


@pytest.fixture
def refresh_token(active_user):
    return RefreshToken.for_user(active_user).__str__()
