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
        'eyJhbGciOiJSUzI1NiIsImtpZCI6ImVmMjQ4ZjQyZjc0YWUwZjk0OTIwYWY5YTlhMD'
        'EzMTdlZjJkMzVmZTEiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL3NlY3VyZ'
        'XRva2VuLmdvb2dsZS5jb20vdm9sbGV5Ym9sbGV5LTkwMDllIiwiYXVkIjoidm9sbGV'
        '5Ym9sbGV5LTkwMDllIiwiYXV0aF90aW1lIjoxNzU2NzQxNzI4LCJ1c2VyX2lkIjoic'
        'TROcTlrM2xXSGhQZnhZUFlVRnNQUlJEeFN0MSIsInN1YiI6InE0TnE5azNsV0hoUGZ'
        '4WVBZVUZzUFJSRHhTdDEiLCJpYXQiOjE3NTY3NDE3MjgsImV4cCI6MTc1Njc0NTMyO'
        'CwicGhvbmVfbnVtYmVyIjoiKzc5MDAwMDAwMDAxIiwiZmlyZWJhc2UiOnsiaWRlbnR'
        'pdGllcyI6eyJwaG9uZSI6WyIrNzkwMDAwMDAwMDEiXX0sInNpZ25faW5fcHJvdmlkZ'
        'XIiOiJwaG9uZSJ9fQ.MGNSQgAS9oKZLGoETPTUVXsil14vrwxAVL3P9rUYHyu7fZ4O'
        'hrgTOZja7C1xL9_MOmSLZJuf1ltf_JcNsec2YuCpP8JGVLyIqbtrARPEZocjOB7iRd'
        'Q2gEHeU0tFG1Irh2PEvDpSPl6bpFzXl9EuR_3KYP49NcdGfNy-Bmclq30266cZI-L1'
        'Laet0ZdkIR3JYzgynrmB4SxDgZ3C1mMFaqhBswyKAn4G8ubRcQ9w7pPpQdcvL3tuA8'
        'y3TCAGwRHbgeXmMZ_Sb_srVMWQ0-qg3oi10lZ1J-iUW5sCfibRiezYLi4X_K-x-vou'
        'zPl6BA6YoXooK9xbpLHZV5UjUeI4aA'
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
