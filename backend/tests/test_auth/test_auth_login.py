from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse, reverse_lazy
from rest_framework import status

User = get_user_model()


@pytest.mark.django_db
def test_get_current_player_unauthorized(api_client):
    url = reverse('api:players-list')
    response = api_client.get(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestGoogleAuth:
    """Test auth with moke google answer."""

    url = reverse_lazy('api:google-login')

    def test_auth_with_google_access_token(
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
            
            self._check_response(response, google_response)

    def test_auth_with_google_id_token(
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
            self._check_response(response, google_response)

    def _check_response(self, response, google_response):
        
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
        assert player_json['first_name'] == google_response.get('given_name')
        assert player_json['last_name'] == google_response.get('family_name')
        assert player_json['gender'] == 'MALE'
        assert player_json['date_of_birth'] == '2000-01-01'
        assert player_json['level'] == 'LIGHT'
        assert player_json['country'] is None
        assert player_json['city'] is None
        assert player_json['is_registered'] is False


@pytest.mark.django_db
class TestPhoneNumberAuth:
    """Test auth with moke firebase answer."""

    url = reverse_lazy('api:phone-number-login')

    def test_auth_with_moke_firebase_response(
        self, api_client, firebase_response
    ):
        with patch(
            'apps.api.utils.firebase_auth.verify_id_token', 
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
            'apps.api.utils.firebase_auth.verify_id_token', 
            return_value=invalid_token
        ):
            response = api_client.post(
                self.url,
                {'id_token': 'fake-firebase-id-token'},
                format='json'
            )
            assert response.status_code == expected_status

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
