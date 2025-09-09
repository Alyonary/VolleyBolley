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
    return (
        'eyJhbGciOiJSUzI1NiIsImtpZCI6ImUzZWU3ZTAyOGUzODg1YTM0NWNlMDcwNTVmODQ2O'
        'DYyMjU1YTcwNDYiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL3NlY3VyZXRva2V'
        'uLmdvb2dsZS5jb20vdm9sbGV5Ym9sbGV5LTkwMDllIiwiYXVkIjoidm9sbGV5Ym9sbGV5'
        'LTkwMDllIiwiYXV0aF90aW1lIjoxNzU3MDg5MDU5LCJ1c2VyX2lkIjoicTROcTlrM2xXS'
        'GhQZnhZUFlVRnNQUlJEeFN0MSIsInN1YiI6InE0TnE5azNsV0hoUGZ4WVBZVUZzUFJSRH'
        'hTdDEiLCJpYXQiOjE3NTcwODkwNTksImV4cCI6MTc1NzA5MjY1OSwicGhvbmVfbnVtYmV'
        'yIjoiKzc5MDAwMDAwMDAxIiwiZmlyZWJhc2UiOnsiaWRlbnRpdGllcyI6eyJwaG9uZSI6'
        'WyIrNzkwMDAwMDAwMDEiXX0sInNpZ25faW5fcHJvdmlkZXIiOiJwaG9uZSJ9fQ.X0Xpv5'
        'D8V3I0PBr46AQN_rGU35IJkgFvkAQRrckAzhhMkPX12VjV0L73czJ5UPkOI-dzklw7ae6'
        'l8jfXeb2cApBD_TsacUmKP1M-n7LZbUzmsUVrPfESF6lLJC3uxp3ZDe3s0xF9RioFH94I'
        'nCCPza9srRoUeCa4GaXpXwXiiYINS8Db26NMPYVQLlsbrdQvVmQoFqrcESf0kIbMSv5El'
        'PeX4ayotuw0glapanQYzk0E8pdPLYqq2thlUb68XbERbV-sKcwLMTgc4Bd6M4plnPFPzE'
        'S4wxJPTRIJSTXSuJunZPh6iBiINv3Po7O91j9d0g2hUsEnWjeFOfYuNIsL0Q'
    )

@pytest.fixture
def invalid_firebase_token():
    return 'invalid-firebase-token'


@pytest.fixture
def refresh_token(active_user):
    return RefreshToken.for_user(active_user).__str__()

@pytest.fixture
def refresh_token_for_user_with_registered_player(user_with_registered_player):
    return RefreshToken.for_user(user_with_registered_player)
