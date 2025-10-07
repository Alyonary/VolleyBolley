import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

from apps.players.models import Player

User = get_user_model()


@pytest.mark.django_db
class TestPlayerRegistration:
    def test_player_registration(
        self,
        auth_api_client_with_not_registered_player,
        player_data_for_registration,
        user_generated_after_login
    ):
        url = reverse('api:players-register')
        response = auth_api_client_with_not_registered_player.post(
           url, player_data_for_registration, format='json'
        )
        player = Player.objects.get(user=user_generated_after_login)
        player.refresh_from_db()
        assert player.rating.grade == player_data_for_registration['level']
        assert response.status_code == status.HTTP_200_OK
        assert response.data is None
        assert player.is_registered is True

    def test_player_registration_with_registered_player(
        self,
        auth_api_client_registered_player,
        player_data_for_registration
    ):
        url = reverse('api:players-register')
        response = auth_api_client_registered_player.post(
           url, player_data_for_registration, format='json'
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
