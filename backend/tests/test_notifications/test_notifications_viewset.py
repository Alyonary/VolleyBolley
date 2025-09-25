import pytest
from rest_framework import status

from apps.notifications.constants import NotificationTypes
from apps.notifications.models import Notifications


@pytest.mark.django_db
class TestNotificationsViewSet:

    def test_permissions_required_auth(self, api_client, notifications_url):
        response = api_client.get(notifications_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        response = api_client.patch(notifications_url, data={}, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_notifications(
        self,
        authenticated_client,
        notifications_url,
        all_notification_types
    ):
        client, user = authenticated_client
        notif1 = Notifications.objects.create(
            player=user.player,
            notification_type=all_notification_types[
                NotificationTypes.GAME_RATE
            ]
        )
        notif2 = Notifications.objects.create(
            player=user.player,
            notification_type=all_notification_types[
                NotificationTypes.GAME_REMINDER
            ]
        )
        notif3 = Notifications.objects.create(
            player=user.player,
            notification_type=all_notification_types[
                NotificationTypes.GAME_REMOVED
            ],
            is_read=True
        )
        response = client.get(notifications_url)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert 'notifications' in data
        ids = [n['notification_id'] for n in data['notifications']]
        assert notif1.id in ids
        assert notif2.id in ids
        assert notif3.id in ids

        expected_keys = {
            'notification_id', 'created_at', 'title', 'message', 'screen'
            }
        for n in data['notifications']:
            assert expected_keys.issubset(set(n.keys()))
            assert isinstance(n['title'], str)
            assert isinstance(n['message'], str)
            assert isinstance(n['screen'], str)

    def test_get_read_notifications(
        self,
        authenticated_client,
        notifications_url,
        notifications_objs
    ):
        client, user = authenticated_client
        response = client.get(notifications_url)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert 'notifications' in data
        assert len(data['notifications']) == 3
        for n in notifications_objs['all_notifications']:
            n.is_read = True
            n.save()
        response = client.get(notifications_url)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert 'notifications' in data
        assert len(data['notifications']) == 0
        
  
        
    def test_patch_notifications_success(
        self,
        authenticated_client,
        notifications_url,
        rate_notification_type,
        in_game_notification_type
    ):
        client, user = authenticated_client
        notif1 = Notifications.objects.create(
            player=user.player, notification_type=rate_notification_type
        )
        notif2 = Notifications.objects.create(
            player=user.player, notification_type=in_game_notification_type
        )
        data = {
            'notifications': [
                {'notification_id': notif1.id},
                {'notification_id': notif2.id},
            ]
        }
        response = client.patch(notifications_url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        notif1.refresh_from_db()
        notif2.refresh_from_db()
        assert notif1.is_read is True
        assert notif2.is_read is True

    def test_patch_notifications_invalid_id(
        self,
        authenticated_client,
        notifications_url,
        rate_notification_type
    ):
        client, user = authenticated_client
        notif1 = Notifications.objects.create(
            player=user.player, notification_type=rate_notification_type
        )
        data = {
            "notifications": [
                {'notification_id': 99999},
                {'notification_id': notif1.id},
            ]
        }
        response = client.patch(notifications_url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        notif1.refresh_from_db()
        assert notif1.is_read is True

    def test_patch_notifications_empty(
        self, authenticated_client, notifications_url
    ):
        client, user = authenticated_client
        data = {'notifications': []}
        response = client.patch(notifications_url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
