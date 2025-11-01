from copy import deepcopy

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

from apps.players.models import Player

User = get_user_model()


@pytest.mark.django_db
class TestPlayerRegistration:

    url = reverse('api:players-register')

    @pytest.mark.parametrize(
        'player_fixture_data,expected_status,registered',
        [
            ('player_data_for_registration', status.HTTP_200_OK, True),
            ('player_no_data_for_registration',
             status.HTTP_400_BAD_REQUEST, False),
            ('player_necessary_data_for_registration',
             status.HTTP_200_OK, True)
        ]
    )
    def test_player_registration(
        self,
        request,
        player_fixture_data,
        expected_status,
        registered,
        auth_api_client_with_not_registered_player,
        player_no_data_for_registration,
        player_necessary_data_for_registration,
        player_generated_after_login_data,
        user_generated_after_login
    ):
        player_data = request.getfixturevalue(player_fixture_data)

        response = auth_api_client_with_not_registered_player.post(
           self.url, player_data, format='json'
        )
        player = Player.objects.get(user=user_generated_after_login)

        assert response.status_code == expected_status
        assert player.is_registered is registered

        if player_data != player_no_data_for_registration:
            assert response.data is None
            assert player.country.id == player_data['country']
            assert player.city.id == player_data['city']
            assert not player.avatar

            if player_data == player_necessary_data_for_registration:
                upcoming_player_data = deepcopy(player_data)
                player_data = deepcopy(player_generated_after_login_data)
                player_data.update(upcoming_player_data)

            assert player.user.first_name == player_data['first_name']
            assert player.user.last_name == player_data['last_name']
            assert player.gender == player_data['gender']
            assert player.date_of_birth.isoformat() == player_data[
                'date_of_birth'
            ]
            assert player.rating.grade == player_data['level']

    def test_player_registration_with_registered_player(
        self,
        auth_api_client_registered_player,
        player_data_for_registration
    ):
        response = auth_api_client_registered_player.post(
           self.url, player_data_for_registration, format='json'
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
