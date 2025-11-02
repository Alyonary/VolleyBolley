import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

User = get_user_model()


@pytest.mark.django_db
class TestTokens:

    def test_jwt_token_refresh(self, api_client, refresh_token):

        response = self._refresh_token(api_client, refresh_token)

        assert response.status_code == status.HTTP_200_OK
        assert 'access_token' in response.data
        assert isinstance(response.data.get('access_token'), str)

    def test_jwt_token_verify(self, api_client, refresh_token):

        url = reverse('api:auth:token-verify')
        access_token = self._refresh_token(
            api_client, refresh_token
        ).data.get('access_token')
        response = api_client.post(url, {'access_token': access_token})

        assert response.status_code == status.HTTP_200_OK

    def _refresh_token(self, client, refresh_token):
        url = reverse('api:auth:token-refresh')
        return client.post(url, {'refresh_token': refresh_token})
