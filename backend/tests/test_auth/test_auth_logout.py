import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken

User = get_user_model()


@pytest.mark.django_db
class TestLogout:
    url = reverse('api:auth:logout')

    def test_logout_success(
        self,
        auth_api_client_registered_player,
        refresh_token_for_user_with_registered_player
    ):
        response = auth_api_client_registered_player.post(
            self.url,
            {
                'refresh_token': str(
                    refresh_token_for_user_with_registered_player
                )
            },
            format='json'
        )

        assert response.status_code == status.HTTP_205_RESET_CONTENT
        assert BlacklistedToken.objects.filter(
            token__jti=refresh_token_for_user_with_registered_player['jti']
        ).exists()

    @pytest.mark.parametrize(
        'token_type, token_value',
        [
            ('refresh_token', 'invalid-token'),
            ('refresh_token', None),
            ('access_token', None),
            (None, None)
        ]
    )
    def test_logout_invalid_token(
        self,
        auth_api_client_registered_player,
        token_type,
        token_value
    ):
        response = auth_api_client_registered_player.post(
            self.url,
            {token_type: token_value},
            format='json'
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
