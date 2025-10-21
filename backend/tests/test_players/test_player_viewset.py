from copy import deepcopy

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

from apps.players.constants import BASE_PAYMENT_DATA, Payments
from apps.players.models import Favorite, Payment, Player

User = get_user_model()


@pytest.mark.django_db
class TestPlayerViewSet:

    @pytest.mark.parametrize(
        'client_fixture_name,expected_status',
        [
            ('api_client', status.HTTP_401_UNAUTHORIZED),
            ('auth_api_client_with_not_registered_player',
             status.HTTP_403_FORBIDDEN),
            ('auth_api_client_registered_player', status.HTTP_200_OK),
        ],
    )
    def test_get_my_profile(
        self, request, client_fixture_name, expected_status
    ):
        client = request.getfixturevalue(client_fixture_name)
        url = reverse('api:players-me')
        response = client.get(url)

        assert response.status_code == expected_status

        if client_fixture_name == 'auth_api_client_registered_player':
            expected_fields = (
                'first_name',
                'last_name',
                'gender',
                'date_of_birth',
                'level',
                'country',
                'city',
                'avatar'
            )
            for field in response.data:
                assert field in expected_fields
            assert len(expected_fields) == len(response.data)

    @pytest.mark.parametrize(
        'client_fixture_name,expected_status',
        [
            ('api_client', status.HTTP_401_UNAUTHORIZED),
            ('auth_api_client_with_not_registered_player',
             status.HTTP_403_FORBIDDEN),
            ('auth_api_client_registered_player', status.HTTP_200_OK),
        ],
    )
    def test_get_player_list(
        self, request, client_fixture_name, expected_status,
    ):
        client = request.getfixturevalue(client_fixture_name)
        url = reverse('api:players-list')

        response = client.get(url)
        assert response.status_code == expected_status

    @pytest.mark.parametrize(
        'client_fixture_name,expected_status',
        [
            ('api_client', status.HTTP_401_UNAUTHORIZED),
            ('auth_api_client_with_not_registered_player',
             status.HTTP_403_FORBIDDEN),
            ('auth_api_client_registered_player', status.HTTP_200_OK),
        ],
    )
    def test_get_player_detail(
        self, request, client_fixture_name, expected_status,
        bulk_create_registered_players
    ):
        client = request.getfixturevalue(client_fixture_name)
        other_player = bulk_create_registered_players[0]
        url = reverse('api:players-detail', args=[other_player.id])
        response = client.get(url)

        assert response.status_code == expected_status
        if client_fixture_name == 'auth_api_client_registered_player':
            assert response.data['first_name'] == other_player.user.first_name
            assert response.data['last_name'] == other_player.user.last_name


    @pytest.mark.parametrize(
        'client_fixture_name,expected_status',
        [
            ('api_client', status.HTTP_401_UNAUTHORIZED),
            ('auth_api_client_with_not_registered_player',
             status.HTTP_403_FORBIDDEN),
            ('auth_api_client_registered_player', status.HTTP_404_NOT_FOUND),
        ],
    )
    def test_get_not_registered_player_detail(
        self, request, client_fixture_name, expected_status,
        bulk_create_not_registered_players
    ):
        client = request.getfixturevalue(client_fixture_name)
        other_player = bulk_create_not_registered_players[0]
        url = reverse('api:players-detail', args=[other_player.id])
        response = client.get(url)

        assert response.status_code == expected_status

    @pytest.mark.parametrize(
        'client_fixture_name,expected_status',
        [
            ('api_client', status.HTTP_401_UNAUTHORIZED),
            ('auth_api_client_with_not_registered_player',
             status.HTTP_403_FORBIDDEN),
            ('auth_api_client_registered_player', status.HTTP_200_OK),
        ],
    )
    def test_status_patch_my_profile(
        self,
        request,
        client_fixture_name,
        expected_status,
        player_updated_data
    ):
        client = request.getfixturevalue(client_fixture_name)
        url = reverse('api:players-me')
        response = client.patch(url, player_updated_data, format='json')

        assert response.status_code == expected_status

    @pytest.mark.parametrize(
        'data',
        [
            'player_updated_data',
            'player_partial_updated_data'
        ]
    )
    def test_patch_my_profile(
        self,
        request,
        data,
        auth_api_client_registered_player,
        registered_player_data,
        player_partial_updated_data
    ):
        data = request.getfixturevalue(data)
        url = reverse('api:players-me')
        response = auth_api_client_registered_player.patch(
            url, data, format='json'
        )
        user = User.objects.get(
            id=response.wsgi_request.user.id
        )

        if data == player_partial_updated_data:
            data = deepcopy(registered_player_data)
            data.update(player_partial_updated_data)

        # allowed to be updated fields
        assert user.first_name == data.get('first_name')
        assert user.last_name == data.get('last_name')
        assert user.player.country.id == data.get('country')
        assert user.player.city.id == data.get('city')
        assert user.player.date_of_birth.isoformat() == data.get(
            'date_of_birth'
        )

        # not allowed to be updated fields
        assert user.player.is_registered is True
        assert not user.player.avatar
        assert user.player.gender == registered_player_data.get('gender')
        assert user.player.rating.grade == registered_player_data.get('level')


    @pytest.mark.parametrize(
        'client_fixture_name,expected_status',
        [
            ('api_client', status.HTTP_401_UNAUTHORIZED),
            ('auth_api_client_with_not_registered_player',
             status.HTTP_403_FORBIDDEN),
            ('auth_api_client_registered_player', status.HTTP_204_NO_CONTENT),
        ],
    )
    def test_delete_my_profile(
        self, request, client_fixture_name, expected_status
    ):
        client = request.getfixturevalue(client_fixture_name)
        url = reverse('api:players-me')
        response = client.delete(url)

        assert response.status_code == expected_status

        if client_fixture_name == 'auth_api_client_registered_player':
            assert not User.objects.filter(
                id=response.wsgi_request.user.id
                ).exists()

    @pytest.mark.parametrize(
        'client_fixture_name,expected_status',
        [
            ('api_client', status.HTTP_401_UNAUTHORIZED),
            ('auth_api_client_with_not_registered_player',
             status.HTTP_403_FORBIDDEN),
            ('auth_api_client_registered_player', status.HTTP_200_OK),
        ],
    )
    def test_put_avatar(
        self, request, client_fixture_name, expected_status
    ):
        client = request.getfixturevalue(client_fixture_name)
        url = reverse('api:players-me-avatar')
        data = {'avatar': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAA'
                          'AABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAA'
                          'AABJRU5ErkJggg=='}

        response = client.put(url, data, format='json')
        assert response.status_code == expected_status

        if client_fixture_name == 'auth_api_client_registered_player':
            assert Player.objects.get(user=response.wsgi_request.user).avatar
            me_url = reverse('api:players-me')
            response = client.get(me_url)
            assert response.data['avatar'].startswith('http')

    @pytest.mark.parametrize(
        'client_fixture_name,expected_status',
        [
            ('api_client', status.HTTP_401_UNAUTHORIZED),
            ('auth_api_client_with_not_registered_player',
             status.HTTP_403_FORBIDDEN),
            ('auth_api_client_registered_player', status.HTTP_200_OK),
        ],
    )
    def test_get_payments(
        self, request, client_fixture_name, expected_status
    ):
        client = request.getfixturevalue(client_fixture_name)
        url = reverse('api:players-me-payments')

        response = client.get(url)
        assert response.status_code == expected_status

        if client_fixture_name == 'auth_api_client_registered_player':
            assert len(response.data['payments']) == len(BASE_PAYMENT_DATA)
            expected_fields = (
                'payment_type',
                'payment_account',
                'is_preferred'
            )
            for payment in response.data['payments']:
                assert any(field in expected_fields for field in payment)
                assert (
                    payment['is_preferred']
                    if payment['payment_type'] == 'CASH'
                    else not payment['is_preferred']
                )

    @pytest.mark.parametrize(
        'client_fixture_name,expected_status',
        [
            ('api_client', status.HTTP_401_UNAUTHORIZED),
            ('auth_api_client_with_not_registered_player',
             status.HTTP_403_FORBIDDEN),
            ('auth_api_client_registered_player', status.HTTP_200_OK),
        ],
    )
    def test_put_payments(
        self, request, client_fixture_name, expected_status,
        user_generated_after_login
    ):
        client = request.getfixturevalue(client_fixture_name)
        url = reverse('api:players-me-payments')
        payment_data = {
            'payments': [
                {
                'payment_type': Payments.THAIBANK.value,
                'payment_account': '1234567890',
                'is_preferred': True
                },
                {
                'payment_type': Payments.REVOLUT.value,
                'payment_account': '1234567890',
                'is_preferred': False
                },
                {
                'payment_type': Payments.CASH.value,
                'payment_account': '1234567890',
                'is_preferred': False
                },
            ]
        }

        response = client.put(url, payment_data, format='json')
        assert response.status_code == expected_status

        if client_fixture_name == 'auth_api_client_registered_player':
            payments = Payment.objects.filter(
                player=user_generated_after_login.player
            )
            for payment in payments:
                assert (payment.is_preferred
                        if payment.payment_type == Payments.THAIBANK.value
                        else not payment.is_preferred)

    @pytest.mark.parametrize(
        'client_fixture_name,expected_status',
        [
            ('api_client', status.HTTP_401_UNAUTHORIZED),
            ('auth_api_client_with_not_registered_player',
             status.HTTP_403_FORBIDDEN),
            ('auth_api_client_registered_player', status.HTTP_400_BAD_REQUEST),
        ],
    )
    def test_put_invalid_payment_type(
        self, request, client_fixture_name, expected_status,
    ):
        client = request.getfixturevalue(client_fixture_name)
        url = reverse('api:players-me-payments')
        invalid_payment_data = {
            'payments': [
                {
                'payment_type': Payments.THAIBANK.value,
                'payment_account': '1234567890',
                'is_preferred': True
                },
                {
                'payment_type': Payments.REVOLUT.value,
                'payment_account': '1234567890',
                'is_preferred': True
                },
                {
                'payment_type': Payments.CASH.value,
                'payment_account': '1234567890',
                'is_preferred': False
                },
            ]
        }

        response = client.put(url, invalid_payment_data, format='json')
        assert response.status_code == expected_status

    @pytest.mark.parametrize(
        'client_fixture_name,expected_status',
        [
            ('auth_api_client_registered_player', status.HTTP_201_CREATED),
            ('api_client', status.HTTP_401_UNAUTHORIZED),
            ('auth_api_client_with_not_registered_player',
             status.HTTP_403_FORBIDDEN),
        ],
    )
    def test_add_favorite(
        self, request, client_fixture_name, expected_status,
        bulk_create_registered_players
    ):
        client = request.getfixturevalue(client_fixture_name)
        other_player = bulk_create_registered_players[0]
        url = reverse('api:players-favorite', args=[other_player.id])

        response = client.post(url)
        assert response.status_code == expected_status

        if client_fixture_name == 'auth_api_client_registered_player':
            assert Favorite.objects.filter(
                player=response.wsgi_request.user.player,
                favorite=other_player
            ).exists()

    @pytest.mark.parametrize(
        'client_fixture_name,expected_status',
        [
            ('api_client', status.HTTP_401_UNAUTHORIZED),
            ('auth_api_client_with_not_registered_player',
             status.HTTP_403_FORBIDDEN),
            ('auth_api_client_registered_player', status.HTTP_204_NO_CONTENT),
        ],
    )
    def test_remove_favorite(
        self, request, client_fixture_name, expected_status,
        user_with_registered_player, bulk_create_registered_players
    ):
        client = request.getfixturevalue(client_fixture_name)
        other_player = bulk_create_registered_players[0]

        if client_fixture_name == 'auth_api_client_registered_player':
            Favorite.objects.create(
                player=user_with_registered_player.player,
                favorite=other_player
            )

        url = reverse('api:players-favorite', args=[other_player.id])
        response = client.delete(url)
        assert response.status_code == expected_status

        if client_fixture_name == 'auth_api_client_registered_player':
            assert not Favorite.objects.filter(
                player=user_with_registered_player.player,
                favorite=other_player
            ).exists()

    @pytest.mark.parametrize(
        'client_fixture_name,expected_status',
        [
            ('auth_api_client_registered_player', status.HTTP_200_OK),
            ('api_client', status.HTTP_401_UNAUTHORIZED),
            ('auth_api_client_with_not_registered_player',
             status.HTTP_403_FORBIDDEN),
        ],
    )
    def test_player_list_excludes_current_user(
        self, request, client_fixture_name, expected_status,
        bulk_create_registered_players
    ):
        client = request.getfixturevalue(client_fixture_name)

        url = reverse('api:players-list')
        response = client.get(url)

        assert response.status_code == expected_status
        if client_fixture_name == 'auth_api_client_registered_player':
            assert len(response.data) == 4
            current_user_id = response.wsgi_request.user.id
            for player in response.data:
                assert player['player_id'] != current_user_id
