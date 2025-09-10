import pytest
from backend.apps.notifications.notifications import NotificationTypes
from rest_framework import status

from apps.notifications.models import Notifications
from apps.players.models import Player


@pytest.mark.django_db
class TestNotificationsViewSet:

    @pytest.fixture()
    def authenticated_player_client(self, authenticated_client):
        client, user = authenticated_client
        player = Player.objects.create(user=user)
        return client, user, player
        
    def test_permissions_required_auth(self, api_client, notifications_url):
        response = api_client.get(notifications_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        response = api_client.patch(notifications_url, data={}, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_notifications(self, authenticated_player_client, notifications_url):
        client, user, player = authenticated_player_client
        notif1 = Notifications.objects.create(player=player, type=NotificationTypes.RATE)
        notif2 = Notifications.objects.create(player=player, type=NotificationTypes.IN_GAME)
        notif3 = Notifications.objects.create(player=player, type=NotificationTypes.REMOVED, is_read=True)
        response = client.get(notifications_url)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert 'notifications' in data
        ids = [n['notification_id'] for n in data['notifications']]
        assert notif1.id in ids
        assert notif2.id in ids
        assert notif3.id not in ids

        for n in data['notifications']:
            assert set(n.keys()) == {'notification_id', 'created_at', 'title', 'message', 'screen'}
            assert isinstance(n['title'], str)
            assert isinstance(n['message'], str)
            assert isinstance(n['screen'], str)

    def test_patch_notifications_success(self, authenticated_player_client, notifications_url):
        client, user, player = authenticated_player_client
        notif1 = Notifications.objects.create(player=player, type=NotificationTypes.RATE)
        notif2 = Notifications.objects.create(player=player, type=NotificationTypes.IN_GAME)
        data = {
            "notifications": [
                {"notification_id": notif1.id},
                {"notification_id": notif2.id}
            ]
        }
        response = client.patch(notifications_url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        notif1.refresh_from_db()
        notif2.refresh_from_db()
        assert notif1.is_read is True
        assert notif2.is_read is True

    def test_patch_notifications_invalid_id(self, authenticated_client, notifications_url):
        client, user, player = authenticated_client
        notif1 = Notifications.objects.create(player=player, type=NotificationTypes.RATE)
        data = {
            "notifications": [
                {"notification_id": 99999},
                {"notification_id": notif1.id}
            ]
        }
        response = client.patch(notifications_url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        notif1.refresh_from_db()
        assert notif1.is_read is True

    def test_patch_notifications_empty(self, authenticated_client, notifications_url):
        client, user, player = authenticated_client
        data = {"notifications": []}
        response = client.patch(notifications_url, data, format='json')
        assert response.status_code == status.HTTP_200_OK