
import pytest
from django.contrib.auth import get_user_model

from apps.notifications.models import Device, DeviceType

User = get_user_model()


@pytest.mark.django_db
class TestDeviceModel:
    """Tests for Device model and Device manager methods."""

    @pytest.fixture(autouse=True)
    def setup(self, players, devices):
        self.players = players
        self.devices = devices

    def test_device_creation(self):
        """Test successful device creation."""
        device = Device.objects.create(
            token='test_token_new',
            player=self.players['player1'],
            is_active=True
        )
        assert device.token == 'test_token_new'
        assert device.player == self.players['player1']
        assert device.is_active is True
        saved_device = Device.objects.get(token='test_token_new')
        assert saved_device is not None

    def test_device_token_uniqueness(self):
        """Test updating device when token already exists."""
        original_device = self.devices['device1']
        original_player = original_device.player
        assert original_player == self.players['player1']

        device, created = Device.objects.update_or_create_token(
            token=original_device.token,
            player=self.players['player2']
        )
        assert not created
        assert device.player == self.players['player2']
        assert device.id == original_device.id
        assert Device.objects.filter(token=original_device.token).count() == 1

    def test_device_deactivation(self):
        """Test device deactivation."""
        device = self.devices['device1']
        device.is_active = False
        device.save()
        updated_device = Device.objects.get(id=device.id)
        assert updated_device.is_active is False
        assert device not in Device.objects.active()

    def test_cascade_deletion(self):
        """Test cascade deletion when player is deleted."""
        player = self.players['player1']
        device_id = self.devices['device1'].id
        player.delete()
        exists = Device.objects.filter(id=device_id).exists()
        assert not exists, 'Device should be deleted when player is deleted'

    def test_multiple_devices_for_player(self):
        """Test creating multiple devices for one player."""
        device1 = Device.objects.create(
            token='multi_token_1',
            player=self.players['player1'],
            is_active=True
        )
        device2 = Device.objects.create(
            token='multi_token_2',
            player=self.players['player1'],
            is_active=True
        )
        player_devices = Device.objects.filter(player=self.players['player1'])
        assert player_devices.count() >= 2
        assert device1 in player_devices
        assert device2 in player_devices

    def test_device_manager_active(self):
        """Test active() method of Device manager."""
        active_devices = Device.objects.active()
        assert active_devices.count() == len(self.devices['active_devices'])
        for device in self.devices['active_devices']:
            assert device in active_devices
        assert self.devices['device3'] not in active_devices

    def test_device_manager_by_player(self):
        """Test by_player() method of Device manager."""
        player3_devices = Device.objects.by_player(self.players['player3'].id)
        assert player3_devices.count() == 1
        assert self.devices['device4'] in player3_devices
        assert self.devices['device3'] not in player3_devices

        player1_devices = Device.objects.by_player(self.players['player1'].id)
        assert player1_devices.count() == 1
        assert self.devices['device1'] in player1_devices

    def test_device_manager_in_game(self, game_for_notification):
        """Test in_game() method of Device manager."""
        import warnings
        with warnings.catch_warnings():
            warnings.filterwarnings(
                'ignore',
                message=(
                    'DateTimeField .* received a naive datetime .* while '
                    'time zone support is active.'
                )
            )
            game = game_for_notification
            game.players.add(self.players['player1'], self.players['player2'])
            qs = Device.objects.in_game(game.id)
            tokens = [d.token for d in qs]
            assert self.devices['device1'].token in tokens
            assert self.devices['device2'].token in tokens
            assert self.devices['device4'].token not in tokens

    def test_update_or_create_token(self):
        """Test update_or_create_token method of Device manager."""
        player = self.players['player1']
        token = 'unique-token-xyz'
        device, created = Device.objects.update_or_create_token(
            token=token,
            player=player,
            platform=DeviceType.IOS,
            is_active=True
        )
        assert created is True
        assert device.token == token
        assert device.player == player
        assert device.platform == DeviceType.IOS
        device2, created2 = Device.objects.update_or_create_token(
            token=token,
            player=player,
            platform=DeviceType.ANDROID,
            is_active=False
        )
        assert created2 is False
        assert device2.token == token
        assert device2.platform == DeviceType.ANDROID
        assert device2.is_active is False
