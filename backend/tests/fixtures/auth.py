import pytest
from rest_framework_simplejwt.tokens import RefreshToken


@pytest.fixture
def google_response():
    '''Moke google-response after token verification.'''
    return {
        'email': 'test@example.com',
        'sub': '1234567890',
        'given_name': 'Test',
        'family_name': 'User',
        'name': 'Test User'
    }

@pytest.fixture
def real_google_id_token():
    return (
        'eyJhbGciOiJSUzI1NiIsImtpZCI6IjJkN2VkMzM4YzBmMTQ1N2IyMTRhMjc0YjVlMGU2N'
        'jdiNDRhNDJkZGUiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL2FjY291bnRzLmd'
        'vb2dsZS5jb20iLCJhenAiOiIyMDM4MzY2Njc1NS04dTg1MG9lbmU2NGNrY2U1aTE5NGQx'
        'cmFnNXN0MHY3My5hcHBzLmdvb2dsZXVzZXJjb250ZW50LmNvbSIsImF1ZCI6IjIwMzgzN'
        'jY2NzU1LTh1ODUwb2VuZTY0Y2tjZTVpMTk0ZDFyYWc1c3QwdjczLmFwcHMuZ29vZ2xldX'
        'NlcmNvbnRlbnQuY29tIiwic3ViIjoiMTA1NjMzNjI2NTY4MTkyMzc0Njg4IiwiZW1haWw'
        'iOiJkb3JvZi5yaWtAZ21haWwuY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsImF0X2hh'
        'c2giOiJjVzVhd1VXWmJuWTNqQUg4SjJfaUJRIiwibmFtZSI6ItCv0YDQvtGB0LvQsNCyI'
        'NCU0L7RgNC-0YTQtdC10LIiLCJwaWN0dXJlIjoiaHR0cHM6Ly9saDMuZ29vZ2xldXNlcm'
        'NvbnRlbnQuY29tL2EvQUNnOG9jTGtMdWJRcHBhbFhXSVdZTm93cTZ0SjVhRm9qR1M5RzQ'
        '4Zl9kR3NXLXdTZzlfQ2l3PXM5Ni1jIiwiZ2l2ZW5fbmFtZSI6ItCv0YDQvtGB0LvQsNCy'
        'IiwiZmFtaWx5X25hbWUiOiLQlNC-0YDQvtGE0LXQtdCyIiwiaWF0IjoxNzU3MjIyMjI0L'
        'CJleHAiOjE3NTcyMjU4MjR9.pd_bkpHBxwQb5dmb82lpJYUPHZ3FtGAP5cDOcrZuNCE4-'
        'rvjYh2cjcDz6ZrffrOQnrX77ZtKRHTY90mV8txL9aJSdK9IuObgzSDJn5xDn2I2lHqWdB'
        'TnUZYqMFoxOQHpX24uFaK0Uaja9BZDgdoIaOYuPhLr_ms8SMLF8_4btLsfYPog2EIxE9l'
        'Es5-8YfEhNhj_Lb_yGc4mmfVkJOX3G_IX2iTIlk-ZvuSnv2p9cb3FrFePuxcAYj4krCaU'
        '2GJT0z9BTUtKLCGXKdRI33aMUcDR2Usd314Uttd1FA764aRS71l1dy0JZZWHCp0k1-c6W'
        'aHY0YSquSQnrcZMXpLLIQ'
    )


@pytest.fixture
def real_google_access_token():
    return (
        'ya29.a0AS3H6NxMiU77W1eQXQtUH51ZfkUk3oH9isPkdIOMge1f-pFtyhOLxBqVBsIvvt'
        'jcsvJ37pclLXlQ1jf4AsIjydW-s7Kkt0SUeRu5CP_R7uRMspmZ1FFwbNNaxSG_nG2Bpxv'
        '5geuNlj0f_l05LYXrHtpAg-krUHqt-egjlPr3DNCHvpPqcxAwVQDedVihATVn3izidE4a'
        'CgYKAWkSARASFQHGX2Min8xeeoJQbR8na0K8RNxXvg0206'
    )


@pytest.fixture
def firebase_response():
    '''Moke firebase response after token verification.'''
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
    '''Moke firebase response after token verification.
    
    Invalid token: no field "user_id" in JSON response.
    '''
    return {
    'iss': 'https://securetoken.google.com/your-project-id',
    'aud': 'your-project-id',
    'auth_time': 1672531200,
    'sub': 'phone-auth-uid-123',
    'phone_number': '+79123456789',
}


@pytest.fixture
def firebase_response_no_phone_number():
    '''Moke firebase response after token verification.
    
    Invalid token: no field "phone_number" in JSON response.
    '''
    return {
    'iss': 'https://securetoken.google.com/your-project-id',
    'aud': 'your-project-id',
    'auth_time': 1672531200,
    'user_id': 'phone-auth-uid-123',
    'sub': 'phone-auth-uid-123',
}


@pytest.fixture
def firebase_response_bad_phone_number():
    '''Moke firebase response after token verification.
    
    Invalid token: bad value in the field "phone_number" in JSON response.
    '''
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
