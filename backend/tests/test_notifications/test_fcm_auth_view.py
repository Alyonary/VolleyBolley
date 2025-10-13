import pytest
from rest_framework import status

from apps.notifications.models import Device, DeviceType
from apps.players.models import Player


@pytest.mark.django_db
class TestFCMApi:
    """Tests for FCM token API."""

    def test_fcm_token_put_success(
        self,
        fcm_token_url,
        auth_api_client_registered_player,
        user_with_registered_player,
        fcm_token_data
    ):
        """Test successful FCM token registration."""
        client = auth_api_client_registered_player
        response = client.put(fcm_token_url, fcm_token_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        device = Device.objects.filter(token=fcm_token_data['token']).first()
        assert device is not None
        assert device.platform == DeviceType.ANDROID
        assert device.player.user == user_with_registered_player
        assert device.is_active is True

    def test_fcm_token_update_existing(
        self,
        fcm_token_url,
        auth_api_client_registered_player,
        user_with_registered_player,
        existing_device
    ):
        """Test updating an existing FCM token."""
        client = auth_api_client_registered_player
        player = Player.objects.get(user=user_with_registered_player)
        token_data = {
            'token': existing_device.token,
            'platform': DeviceType.ANDROID,
        }
        response = client.put(fcm_token_url, token_data, format='json')
        assert response.status_code == status.HTTP_200_OK
        device = Device.objects.get(token=existing_device.token)
        assert device.player.id == player.id
        assert device.platform == DeviceType.ANDROID

    def test_fcm_token_invalid_data(
        self,
        fcm_token_url,
        auth_api_client_registered_player,
        invalid_fcm_token_data
    ):
        """Test FCM token registration with invalid data."""
        client = auth_api_client_registered_player
        response = client.put(
            fcm_token_url, invalid_fcm_token_data[0], format='json'
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response = client.put(
            fcm_token_url, invalid_fcm_token_data[1], format='json'
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_fcm_token_unauthenticated(
        self,
        fcm_token_url,
        fcm_token_data,
        api_client
    ):
        """Test FCM token registration for unauthenticated user."""

        response = api_client.put(
            fcm_token_url, fcm_token_data, format='json'
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_api_allowed_methods(
        self, fcm_token_url, auth_api_client_registered_player, fcm_token_data
    ):
        """Test that only PUT method is allowed for FCM token endpoint."""
        client = auth_api_client_registered_player

        response = client.get(fcm_token_url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

        response = client.post(fcm_token_url, fcm_token_data)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

        response = client.delete(fcm_token_url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

        response = client.patch(fcm_token_url, fcm_token_data)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        
        response = client.put(fcm_token_url, fcm_token_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED

    def test_fcm_token_empty_platform(
        self, fcm_token_url, auth_api_client_registered_player, fcm_token_data
    ):
        """Test FCM token registration with empty platform."""
        token_without_platform = fcm_token_data.copy()
        token_without_platform.pop('platform', None)
        client = auth_api_client_registered_player

        response = client.put(
            fcm_token_url, token_without_platform, format='json'
        )
        assert response.status_code == status.HTTP_201_CREATED

        device = Device.objects.get(token=token_without_platform['token'])
        assert device.platform is not None
