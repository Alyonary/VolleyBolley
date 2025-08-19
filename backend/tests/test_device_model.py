import pytest

from apps.notifications.models import Device


@pytest.mark.django_db
class TestDeviceModel:
    '''Tests for Device model.'''

    def test_device_creation(self, players):
        '''Test successful device creation.'''
        device = Device.objects.create(
            token='test_token_new',
            player=players['player1'],
            is_active=True
        )
        
        assert device.token == 'test_token_new'
        assert device.player == players['player1']
        assert device.is_active is True
        
        saved_device = Device.objects.get(token='test_token_new')
        assert saved_device is not None
        
    def test_device_token_uniqueness(self, players, devices):
        '''Test updating device when token already exists.'''
        original_device = devices['device1']
        original_player = original_device.player
        assert original_player == players['player1']
        
        device, created = Device.objects.update_or_create_token(
            token=original_device.token,
            player=players['player2']
        )
        
        assert not created
        assert device.player == players['player2']
        assert device.id == original_device.id
        assert Device.objects.filter(token=original_device.token).count() == 1

    def test_device_manager_active(self, devices):
        '''Test active() method of Device manager.'''
        active_devices = Device.objects.active()
        
        assert active_devices.count() == len(devices['active_devices'])
        
        for device in devices['active_devices']:
            assert device in active_devices
        
        assert devices['device3'] not in active_devices
    
    def test_device_manager_by_player(self, players, devices):
        '''Test by_player() method of Device manager.'''
        player3_devices = Device.objects.by_player(players['player3'].id)
        
        assert player3_devices.count() == 1
        assert devices['device4'] in player3_devices
        assert devices['device3'] not in player3_devices
        
        player1_devices = Device.objects.by_player(players['player1'].id)
        assert player1_devices.count() == 1
        assert devices['device1'] in player1_devices
    
    
    def test_device_deactivation(self, devices):
        '''Test device deactivation.'''
        device = devices['device1']
        device.is_active = False
        device.save()
        
        updated_device = Device.objects.get(id=device.id)
        assert updated_device.is_active is False
        assert device not in Device.objects.active()
    
    def test_cascade_deletion(self, players, devices):
        '''Test cascade deletion when player is deleted.'''
        player = players['player1']
        device_id = devices['device1'].id
        player.delete()
        exists = Device.objects.filter(id=device_id).exists()
        assert not exists, 'Device should be deleted when player is deleted'
    
    def test_multiple_devices_for_player(self, players):
        '''Test creating multiple devices for one player.'''
        device1 = Device.objects.create(
            token='multi_token_1',
            player=players['player1'],
            is_active=True
        )
        
        device2 = Device.objects.create(
            token='multi_token_2',
            player=players['player1'],
            is_active=True
        )
        
        player_devices = Device.objects.filter(player=players['player1'])
        assert player_devices.count() >= 2
        assert device1 in player_devices
        assert device2 in player_devices