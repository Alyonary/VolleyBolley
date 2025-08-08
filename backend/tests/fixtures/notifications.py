import pytest
from django.contrib.auth import get_user_model

from apps.notifications.models import Device
from apps.players.models import Player

User = get_user_model()


@pytest.fixture
def users():
    '''Creates test users.'''
    user1 = User.objects.create_user(
        username='testuser1',
        email='test1@example.com',
        password='testpass123'
    )
    user2 = User.objects.create_user(
        username='testuser2',
        email='test2@example.com',
        password='testpass123'
    )
    user3 = User.objects.create_user(
        username='testuser3',
        email='test3@example.com',
        password='testpass123'
    )
    
    return {'user1': user1, 'user2': user2, 'user3': user3}

@pytest.fixture
def players(users):
    '''Creates test players associated with users.'''
    player1 = Player.objects.create(user=users['user1'])
    player2 = Player.objects.create(user=users['user2'])
    player3 = Player.objects.create(user=users['user3'])
    
    return {'player1': player1, 'player2': player2, 'player3': player3}


@pytest.fixture
def devices(players):
    '''Creates test devices for different players.'''
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
def device_tokens(devices):
    '''Returns only device tokens for easier testing.'''
    return {
        'active_tokens': [d.token for d in devices['active_devices']],
        'all_tokens': [d.token for d in devices['all_devices']]
    }