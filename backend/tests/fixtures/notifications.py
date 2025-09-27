from random import choice

import pytest
from django.contrib.auth import get_user_model

from apps.notifications.constants import (
    NOTIFICATION_INIT_DATA,
    NotificationTypes,
)
from apps.notifications.models import (
    Device,
    DeviceType,
    Notifications,
    NotificationsBase,
)
from apps.players.models import Player

User = get_user_model()


@pytest.fixture
def users():
    """Creates test users."""
    user1 = User.objects.create(
        username='test_user1',
        email='test1@example.com',
        password='testpass123'
    )
    user2 = User.objects.create(
        username='test_user2',
        email='test2@example.com',
        password='testpass123'
    )
    user3 = User.objects.create(
        username='test_user3',
        email='test3@example.com',
        password='testpass123'
    )
    user4 = User.objects.create(
        username='test_user4',
        email='test4@example.com',
        password='testpass123'
    )
    user5 = User.objects.create(
        username='test_user5',
        email='test5@example.com',
        password='testpass123'
    )
    user6 = User.objects.create(
        username='test_user6',
        email='test6@example.com',
        password='testpass123'
    )

    return {
        'user1': user1, 'user2': user2, 'user3': user3,
        'user4': user4, 'user5': user5, 'user6': user6
    }

@pytest.fixture
def players(users):
    """Creates test players associated with users."""
    player1 = Player.objects.create(user=users['user1'], is_registered=True)
    player2 = Player.objects.create(user=users['user2'], is_registered=True)
    player3 = Player.objects.create(user=users['user3'], is_registered=True)
    player4 = Player.objects.create(user=users['user4'], is_registered=True)
    player5 = Player.objects.create(user=users['user5'], is_registered=True)
    player6 = Player.objects.create(user=users['user6'], is_registered=True)
    
    return {
        'player1': player1, 'player2': player2, 'player3': player3,
        'player4': player4, 'player5': player5, 'player6': player6
    }


@pytest.fixture
def devices(players):
    """Creates test devices for different players."""
    device1 = Device.objects.create(
        token='fcm_test_token_1',
        player=players['player1'],
        is_active=True
    )
    
    device2 = Device.objects.create(
        token='fcm_test_token_2',
        player=players['player2'],
        is_active=True
    )
    
    device3 = Device.objects.create(
        token='fcm_test_token_3',
        player=players['player3'],
        is_active=False
    )
    
    device4 = Device.objects.create(
        token='fcm_test_token_4',
        player=players['player3'],
        is_active=True
    )
    
    return {
        'device1': device1,
        'device2': device2,
        'device3': device3,
        'device4': device4,
        'all_devices': [device1, device2, device3, device4],
        'active_devices': [device1, device2, device4]
    }

@pytest.fixture
def sample_device(devices):
    """Returns a sample device for testing."""
    return devices['device1']


@pytest.fixture
def device_tokens(devices):
    """Returns only device tokens for easier testing."""
    return {
        'active_tokens': [d.token for d in devices['active_devices']],
        'all_tokens': [d.token for d in devices['all_devices']]
    }

@pytest.fixture
def fcm_token_data():
    """Returns a sample token data for FCM API tests."""
    return {
            'token': 'fcm-test-token-123',
            'platform': DeviceType.ANDROID
        }

@pytest.fixture
def fcm_token_url():
    """Returns the URL for FCM token API."""
    return '/api/notifications/fcm-auth/'


@pytest.fixture
def notifications_url():
    """Returns the URL for notifications API."""
    return '/api/notifications/'


@pytest.fixture
def user_with_player():
    """Create a user with player profile."""
    user = User.objects.create_user(
        username='testuser')
    
    player = Player.objects.create(
        user=user,
        is_registered=True
    )
    return user, player


@pytest.fixture
def second_user_with_player():
    """Create a second user with player profile."""
    user = User.objects.create_user(
        username='another',
        email='another@example.com',
        password='password123'
    )
    player = Player.objects.create(
        user=user,
        is_registered=True
    )
    return user, player


@pytest.fixture
def existing_device(second_user_with_player):
    """Create an existing device for the second user."""
    _, player = second_user_with_player
    token = 'existing-fcm-token'
    device = Device.objects.create(
        token=token,
        player=player,
        platform=DeviceType.IOS
    )
    return device


@pytest.fixture
def invalid_fcm_token_data():
    """Returns invalid FCM token data for testing."""
    return [
        {'platform': DeviceType.ANDROID},
        {'token': 'some-token', 'platform': 'invalid'}
    ]

@pytest.fixture
def all_notification_types(db):
    notifications_objs = {}
    for notif_type, data in NOTIFICATION_INIT_DATA.items():
        obj, _ = NotificationsBase.objects.get_or_create(
            type=notif_type,
            defaults={
                'title': data['title'],
                'body': data['body'],
                'screen': data['screen']
            }
        )
        notifications_objs[notif_type] = obj
    return notifications_objs

@pytest.fixture
def rate_notification_type(all_notification_types):
    return all_notification_types.get(NotificationTypes.GAME_RATE)

@pytest.fixture
def remove_notification_type(all_notification_types):
    return all_notification_types.get(NotificationTypes.GAME_REMOVED)

@pytest.fixture
def in_game_notification_type(all_notification_types):
    obj = all_notification_types.get(NotificationTypes.GAME_REMINDER)
    assert obj is not None, "GAME_REMINDER notification type not found in DB"
    return obj

@pytest.fixture
def sample_notification(
    rate_notification_type,
    remove_notification_type,
    in_game_notification_type
):
    """Returns a random NotificationsBase instance."""
    return choice(
        [
            rate_notification_type,
            remove_notification_type,
            in_game_notification_type
        ]
    )

@pytest.fixture
def notifications_objs(
    authenticated_client,
    rate_notification_type,
    in_game_notification_type,
    remove_notification_type
):
    client, user = authenticated_client
    notif1 = Notifications.objects.create(
        player=user.player, notification_type=rate_notification_type
    )
    notif2 = Notifications.objects.create(
        player=user.player, notification_type=in_game_notification_type
    )
    notif3 = Notifications.objects.create(
        player=user.player, notification_type=remove_notification_type,
    )
    return {
        'notif1': notif1,
        'notif2': notif2,
        'notif3': notif3,
        'all_notifications': [notif1, notif2, notif3],
        'unread_notifications': [notif1, notif2]
    }
    
@pytest.fixture
def game_for_notification(game_thailand):
    return game_thailand
