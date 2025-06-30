import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


@pytest.mark.django_db
class TestDjoserEndpoints:

    def test_get_current_user_unauthorized(self, api_client):
        url = '/api/auth/users/me/'
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_current_user_authorized(self, api_client, active_user):
        url = '/api/auth/users/me/'
        api_client.force_authenticate(user=active_user)
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['username'] == active_user.username

    @pytest.mark.parametrize(
        "test_case, username, password, expected_status",
        [
            # Вход активного пользователя с валидными данными
            ("valid_credentials", "testuser","TestPass123",
             status.HTTP_200_OK),
            # Вход без логина
            ("no_username", None, "TestPass123",
             status.HTTP_400_BAD_REQUEST),
            # Вход без пароля
            ("no_password", "testuser", None,
             status.HTTP_400_BAD_REQUEST),
            # Вход с неправильным логином
            ("wrong_username", "wronguser", "TestPass123",
             status.HTTP_401_UNAUTHORIZED),
            # Вход с неправильным паролем
            ("wrong_password", "testuser", "WrongPass123",
             status.HTTP_401_UNAUTHORIZED),
        ]
    )
    def test_jwt_token_create(
        self, test_case, active_user, api_client, username, password,
        expected_status,
    ):
        url = '/api/auth/jwt/create/'
        data = {}
        if username is not None:
            data['username'] = (
                username if test_case != "valid_credentials"
                else active_user.username
            )
        if password is not None:
            data['password'] = (
                password if test_case != "valid_credentials"
                else 'TestPass123'
            )

        response = api_client.post(url, data)
        assert response.status_code == expected_status
        if expected_status == status.HTTP_200_OK:
            assert 'access' in response.data
            assert 'refresh' in response.data
        elif expected_status == status.HTTP_400_BAD_REQUEST:
            if not username:
                assert 'username' in response.data
            if not password:
                assert 'password' in response.data

    def test_jwt_token_refresh(self, api_client, active_user):
        # First get a refresh token
        token_url = '/api/auth/jwt/create/'
        data = {
            'username': active_user.username,
            'password': 'TestPass123',
        }
        token_response = api_client.post(token_url, data)
        refresh_token = token_response.data['refresh']

        # Now test refresh
        refresh_url = '/api/auth/jwt/refresh/'
        response = api_client.post(refresh_url, {'refresh': refresh_token})
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data

    def test_jwt_token_verify(self, api_client, active_user):
        # First get an access token
        token_url = '/api/auth/jwt/create/'
        data = {
            'username': active_user.username,
            'password': 'TestPass123',
        }
        token_response = api_client.post(token_url, data)
        access_token = token_response.data['access']

        # Now test verify
        verify_url = '/api/auth/jwt/verify/'
        response = api_client.post(verify_url, {'token': access_token})
        assert response.status_code == status.HTTP_200_OK

    def test_user_logout(self, api_client, active_user):
        refresh = RefreshToken.for_user(active_user)

        # Отправляем запрос на выход
        response = api_client.post(
            '/api/auth/logout/',
            {'refresh': str(refresh)},
            format='json'
        )
        print(response.data)
        assert response.status_code == status.HTTP_205_RESET_CONTENT

        # Проверяем, что токен добавлен в черный список
        assert BlacklistedToken.objects.filter(
            token__jti=refresh['jti']
        ).exists()
