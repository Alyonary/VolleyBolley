from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse, reverse_lazy
from rest_framework import status

from apps.players.models import Player

User = get_user_model()


@pytest.mark.django_db
def test_get_current_player_unauthorized(api_client):
    url = reverse('api:players-list')
    response = api_client.get(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestGoogleAuth:
    """Test auth with moke google answer."""

    url = reverse_lazy('api:auth:google-login')

    @pytest.mark.skip(reason="skipped until fresh token will be provided")
    def test_auth_with_id_token_real_google_response(
        self, auth_api_client_with_not_registered_player,
        real_google_id_token
    ):
        response = auth_api_client_with_not_registered_player.post(
            self.url,
            {'id_token': real_google_id_token}
        )
        self._check_response(response)

    @pytest.mark.skip(reason="skipped until fresh token will be provided")
    def test_auth_with_access_token_real_google_response(
        self, auth_api_client_with_not_registered_player,
        real_google_access_token
    ):
        response = auth_api_client_with_not_registered_player.post(
            self.url,
            {'access_token': real_google_access_token}
        )
        self._check_response(response)

    def test_auth_with_google_access_token_moke_google_response(
        self, api_client, google_response
    ):
        with patch(
            'social_core.backends.google.GoogleOAuth2.user_data',
            return_value=google_response
        ):
            response = api_client.post(
                self.url,
                {'access_token': 'fake-google-access-token'},
                format='json'
            )
            self._check_response(response)
            self._check_moke_data_response(response, google_response)

    def test_auth_with_google_id_token_moke_google_response(
        self, api_client, google_response
    ):
        with patch(
            'google.oauth2.id_token.verify_oauth2_token',
            return_value=google_response
        ):
            response = api_client.post(
                self.url,
                {'id_token': 'fake-google-id-token'},
                format='json'
            )
            self._check_response(response)
            self._check_moke_data_response(response, google_response)

    def _check_response(self, response):

        assert response.status_code == status.HTTP_200_OK
        access_token = response.data.get('access_token', None)
        refresh_token = response.data.get('refresh_token', None)
        player_json = response.data.get('player', None)
        assert isinstance(access_token, str)
        assert isinstance(refresh_token, str)
        expected_keys = {
            'player_id',
            'avatar',
            'first_name',
            'last_name',
            'gender',
            'date_of_birth',
            'level',
            'country',
            'city',
            'is_registered'
        }
        for key in expected_keys:
            assert key in player_json
        assert player_json['avatar'] is None
        assert player_json['gender'] == 'MALE'
        assert player_json['date_of_birth'] == '2000-01-01'
        assert player_json['level'] == 'LIGHT'
        assert player_json['country'] is None
        assert player_json['city'] is None
        assert player_json['is_registered'] is False

    def _check_moke_data_response(self, response, google_response):
        player_json = response.data.get('player', None)
        assert player_json['first_name'] == google_response.get('given_name')
        assert player_json['last_name'] == google_response.get('family_name')

    @pytest.mark.parametrize(
        'token_type, token_value, expected_status',
        [
            ('access_token', 'invalid-google-token',
             status.HTTP_400_BAD_REQUEST),
            ('id_token', 'invalid-google-id-token',
             status.HTTP_400_BAD_REQUEST),
            ('access_token', '', status.HTTP_400_BAD_REQUEST),
            ('id_token', '', status.HTTP_400_BAD_REQUEST),
            (None, None, status.HTTP_400_BAD_REQUEST)
        ]
    )
    def test_auth_with_invalid_google_token(
        self, api_client, token_type, token_value, expected_status
    ):
        data = {}
        if token_type:
            data[token_type] = token_value

        response = api_client.post(
            self.url,
            data,
            format='json'
        )
        assert response.status_code == expected_status

    @pytest.mark.parametrize(
        'invalid_google_response, expected_status',
        [
            ({'email': None}, status.HTTP_400_BAD_REQUEST),
            ({'given_name': None, 'family_name': None},
             status.HTTP_400_BAD_REQUEST),
            ({'email': 'invalid-email'}, status.HTTP_400_BAD_REQUEST)
        ]
    )
    def test_auth_with_invalid_moke_google_response(
        self, api_client, invalid_google_response, expected_status
    ):
        with patch(
            'google.oauth2.id_token.verify_oauth2_token',
            return_value=invalid_google_response
        ):
            response = api_client.post(
                self.url,
                {'id_token': 'fake-google-id-token'},
                format='json'
            )
            assert response.status_code == expected_status

    def test_auth_with_valid_moke_google_response(
        self, api_client, google_response
    ):
        with patch(
            'google.oauth2.id_token.verify_oauth2_token',
            return_value=google_response
        ):
            response = api_client.post(
                self.url,
                {'id_token': 'fake-google-id-token'},
                format='json'
            )
            self._check_response(response)
            self._check_moke_data_response(response, google_response)


@pytest.mark.django_db
class TestPhoneNumberAuth:
    """Test auth with moke firebase answer."""

    url = reverse_lazy('api:auth:phone-number-login')

    def test_auth_with_moke_firebase_response(
        self, api_client, firebase_response
    ):
        with patch(
            'apps.authentication.utils.firebase_auth.verify_id_token',
            return_value=firebase_response
        ):
            response = api_client.post(
                self.url,
                {'id_token': 'fake-firebase-id-token'},
                format='json'
            )

            self._check_response(response)

    def _check_response(self, response):

        assert response.status_code == status.HTTP_200_OK
        access_token = response.data.get('access_token', None)
        refresh_token = response.data.get('refresh_token', None)
        player_json = response.data.get('player', None)
        assert isinstance(access_token, str)
        assert isinstance(refresh_token, str)
        expected_keys = {
            'player_id',
            'avatar',
            'first_name',
            'last_name',
            'gender',
            'date_of_birth',
            'level',
            'country',
            'city',
            'is_registered'
        }
        user = Player.objects.filter(pk=player_json['player_id']).first().user
        for key in expected_keys:
            assert key in player_json
        assert player_json['avatar'] is None
        assert player_json['first_name'] == 'Anonym'
        assert player_json['last_name'] == 'Anonym'
        assert player_json['gender'] == 'MALE'
        assert player_json['date_of_birth'] == '2000-01-01'
        assert player_json['level'] == 'LIGHT'
        assert player_json['country'] is None
        assert player_json['city'] is None
        assert player_json['is_registered'] is False
        assert user.username == user.phone_number

    @pytest.mark.parametrize(
        'invalid_token_fixture,expected_status',
        [
            ('firebase_response_no_user_id', status.HTTP_400_BAD_REQUEST),
            ('firebase_response_no_phone_number', status.HTTP_400_BAD_REQUEST),
            ('firebase_response_bad_phone_number',
             status.HTTP_400_BAD_REQUEST),
            ('empty_token', status.HTTP_400_BAD_REQUEST)
        ]
    )
    def test_auth_with_invalid_firebase_token_and_moke_response(
        self, request, api_client, invalid_token_fixture, expected_status
    ):
        invalid_token = request.getfixturevalue(invalid_token_fixture)
        with patch(
            'apps.authentication.utils.firebase_auth.verify_id_token',
            return_value=invalid_token
        ):
            response = api_client.post(
                self.url,
                {'id_token': 'fake-firebase-id-token'},
                format='json'
            )
            assert response.status_code == expected_status

    @pytest.mark.skip(reason="skipped until fresh token will be provided")
    def test_auth_with_real_firebase_token(
        self, api_client, real_firebase_token
    ):

        response = api_client.post(
                self.url,
                {'id_token': real_firebase_token},
                format='json'
            )

        self._check_response(response)

    def test_auth_with_invalid_firebase_token(
        self, api_client, invalid_firebase_token
    ):
        response = api_client.post(
            self.url,
            {'id_token': invalid_firebase_token},
            format='json'
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestFacebookAuth:
    """Test auth with moke firebase answer."""

    url = reverse_lazy('api:auth:facebook-login')

    def test_auth_with_invalid_firebase_token(
        self, api_client, invalid_firebase_token
    ):
        response = api_client.post(
            self.url,
            {'id_token': invalid_firebase_token},
            format='json'
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.skip(reason="skipped until fresh token will be provided")
    def test_auth_with_real_firebase_token(
        self, api_client, real_fb_firebase_token
    ):

        response = api_client.post(
                self.url,
                {'id_token': real_fb_firebase_token},
                format='json'
            )

        self._check_response(response)

    def _check_response(self, response):

        assert response.status_code == status.HTTP_200_OK
        access_token = response.data.get('access_token', None)
        refresh_token = response.data.get('refresh_token', None)
        player_json = response.data.get('player', None)
        assert isinstance(access_token, str)
        assert isinstance(refresh_token, str)
        expected_keys = {
            'player_id',
            'avatar',
            'first_name',
            'last_name',
            'gender',
            'date_of_birth',
            'level',
            'country',
            'city',
            'is_registered'
        }
        for key in expected_keys:
            assert key in player_json
        assert player_json['avatar'] is None
        assert player_json['gender'] == 'MALE'
        assert player_json['date_of_birth'] == '2000-01-01'
        assert player_json['level'] == 'LIGHT'
        assert player_json['country'] is None
        assert player_json['city'] is None
        assert player_json['is_registered'] is False

    @pytest.mark.parametrize(
        'invalid_token_fixture,expected_status',
        [
            ('firebase_fb_response_no_email', status.HTTP_400_BAD_REQUEST),
            ('firebase_fb_response_bad_email', status.HTTP_400_BAD_REQUEST),
            ('empty_token', status.HTTP_400_BAD_REQUEST)
        ]
    )
    def test_auth_with_invalid_firebase_token_and_moke_response(
        self, request, api_client, invalid_token_fixture, expected_status
    ):
        invalid_token = request.getfixturevalue(invalid_token_fixture)
        with patch(
            'apps.authentication.utils.firebase_auth.verify_id_token',
            return_value=invalid_token
        ):
            response = api_client.post(
                self.url,
                {'id_token': 'fake-firebase-id-token'},
                format='json'
            )
            assert response.status_code == expected_status

    def test_auth_with_moke_firebase_response(
        self, api_client, firebase_fb_response
    ):
        with patch(
            'apps.authentication.utils.firebase_auth.verify_id_token',
            return_value=firebase_fb_response
        ):
            response = api_client.post(
                self.url,
                {'id_token': 'fake-firebase-id-token'},
                format='json'
            )

            self._check_response(response)
            assert response.data.get('player').get('first_name') == 'Test'
            assert response.data.get('player').get('last_name') == 'User'


@pytest.mark.django_db
class TestFirebaseGoogleAuth:
    """Test auth with moke firebase answer."""

    url = reverse_lazy('api:auth:google-login-v2')

    def test_auth_with_invalid_firebase_token(
        self, api_client, invalid_firebase_token
    ):
        response = api_client.post(
            self.url,
            {'id_token': invalid_firebase_token},
            format='json'
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.skip(reason="skipped until fresh token will be provided")
    def test_auth_with_real_firebase_token(
        self, api_client, real_fb_firebase_token
    ):

        response = api_client.post(
                self.url,
                {'id_token': real_fb_firebase_token},
                format='json'
            )

        self._check_response(response)

    def _check_response(self, response):

        assert response.status_code == status.HTTP_200_OK
        access_token = response.data.get('access_token', None)
        refresh_token = response.data.get('refresh_token', None)
        player_json = response.data.get('player', None)
        assert isinstance(access_token, str)
        assert isinstance(refresh_token, str)
        expected_keys = {
            'player_id',
            'avatar',
            'first_name',
            'last_name',
            'gender',
            'date_of_birth',
            'level',
            'country',
            'city',
            'is_registered'
        }
        for key in expected_keys:
            assert key in player_json
        assert player_json['avatar'] is None
        assert player_json['gender'] == 'MALE'
        assert player_json['date_of_birth'] == '2000-01-01'
        assert player_json['level'] == 'LIGHT'
        assert player_json['country'] is None
        assert player_json['city'] is None
        assert player_json['is_registered'] is False

    @pytest.mark.parametrize(
        'invalid_token_fixture,expected_status',
        [
            ('firebase_fb_response_no_email', status.HTTP_400_BAD_REQUEST),
            ('firebase_fb_response_bad_email', status.HTTP_400_BAD_REQUEST),
            ('empty_token', status.HTTP_400_BAD_REQUEST)
        ]
    )
    def test_auth_with_invalid_firebase_token_and_moke_response(
        self, request, api_client, invalid_token_fixture, expected_status
    ):
        invalid_token = request.getfixturevalue(invalid_token_fixture)
        with patch(
            'apps.authentication.utils.firebase_auth.verify_id_token',
            return_value=invalid_token
        ):
            response = api_client.post(
                self.url,
                {'id_token': 'fake-firebase-id-token'},
                format='json'
            )
            assert response.status_code == expected_status

    def test_auth_with_moke_firebase_response(
        self, api_client, firebase_fb_response
    ):
        with patch(
            'apps.authentication.utils.firebase_auth.verify_id_token',
            return_value=firebase_fb_response
        ):
            response = api_client.post(
                self.url,
                {'id_token': 'fake-firebase-id-token'},
                format='json'
            )

            self._check_response(response)
            assert response.data.get('player').get('first_name') == 'Test'
            assert response.data.get('player').get('last_name') == 'User'
