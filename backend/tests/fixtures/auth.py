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
def firebase_response():
    return {
    'iss': 'https://securetoken.google.com/your-project-id',
    'aud': 'your-project-id',
    'auth_time': 1672531200,
    'user_id': 'phone-auth-uid-123',
    'sub': 'phone-auth-uid-123',
    'phone_number': '+79123456789',
}


@pytest.fixture
def firebase_response_no_user_id():
    return {
    'iss': 'https://securetoken.google.com/your-project-id',
    'aud': 'your-project-id',
    'auth_time': 1672531200,
    'sub': 'phone-auth-uid-123',
    'phone_number': '+79123456789',
}


@pytest.fixture
def firebase_response_no_phone_number():
    return {
    'iss': 'https://securetoken.google.com/your-project-id',
    'aud': 'your-project-id',
    'auth_time': 1672531200,
    'user_id': 'phone-auth-uid-123',
    'sub': 'phone-auth-uid-123',
}


@pytest.fixture
def firebase_response_bad_phone_number():
    return {
    'iss': 'https://securetoken.google.com/your-project-id',
    'aud': 'your-project-id',
    'auth_time': 1672531200,
    'user_id': 'phone-auth-uid-123',
    'sub': 'phone-auth-uid-123',
    'phone_number': 'bad_phone_number',
}


@pytest.fixture
def empty_token():
    return {}


@pytest.fixture
def real_firebase_token():
    return 'put-here-real-firebase-token'

@pytest.fixture
def invalid_firebase_token():
    return 'invalid-firebase-token'


@pytest.fixture
def refresh_token(active_user):
    return RefreshToken.for_user(active_user).__str__()
