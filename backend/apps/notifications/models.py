from cryptography.fernet import Fernet
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.event.models import Game
from apps.notifications.constants import DEVICE_MAX_LENGTH
from apps.players.models import Player


class DeviceManager(models.Manager):
    '''Custom manager for Device model.'''

    def active(self):
        '''Return only active devices.'''
        return self.get_queryset().filter(is_active=True)

    def in_game(self, game_id):
        '''Return devices associated with players in a specific game.'''
        game = Game.objects.get(id=game_id)
        user_ids = game.players.values_list('id', flat=True)
        player_ids = Player.objects.filter(
            user_id__in=user_ids
        ).values_list('id', flat=True)
        return self.active().filter(player_id__in=player_ids)

    def by_player(self, player_id):
        '''Return devices associated with a specific player.'''
        return self.active(
            ).filter(player_id=player_id)

    def update_or_create_token(self, token, player, is_active=True):
        '''
        Update or create a device with the given token and player.
        If a device with the token already exists, it updates the player
        and active status. If it doesn't exist, it creates a new device.
        Returns the device and a boolean indicating if it was created.
        '''
        try:
            device = self.get(token=token)
            device.player = player
            device.is_active = is_active
            device.save()
            return device, False
        except self.model.DoesNotExist:
            device = self.create(
                token=token,
                player=player,
                is_active=is_active
            )
            return device, True


class DeviceType(models.TextChoices):
    IOS = 'ios', 'ios'
    ANDROID = 'android', 'android'
    WEB = 'web', 'web'


class EncryptedTokenField(models.CharField):
    """
    Field that automatically encrypts/decrypts device tokens.
    """
    
    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = DEVICE_MAX_LENGTH * 2
        super().__init__(*args, **kwargs)
    
    def get_prep_value(self, value):
        """Encrypts value before saving to DB."""
        if value is None:
            return value
            
        cipher_suite = Fernet(settings.ENCRYPTION_KEY.encode())
        encrypted_token = cipher_suite.encrypt(value.encode('utf-8'))
        return encrypted_token.decode('utf-8')
    
    def from_db_value(self, value, expression, connection):
        """Decrypts value when retrieved from DB."""
        if value is None:
            return value
        cipher_suite = Fernet(settings.ENCRYPTION_KEY.encode())
        try:
            decrypted_token = cipher_suite.decrypt(value.encode('utf-8'))
            return decrypted_token.decode('utf-8')
        except Exception:
            return value


class Device(models.Model):
    '''Model for storing device information for push notifications.'''
    token = EncryptedTokenField(unique=True)
    platform = models.CharField(
        max_length=10,
        choices=DeviceType.choices,
        default=DeviceType.ANDROID
    )
    player = models.ForeignKey(
        'players.Player',
        related_name='devices',
        on_delete=models.CASCADE
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = DeviceManager()

    class Meta:
        verbose_name = _('Device')
        verbose_name_plural = _('Devices')

    def __str__(self):
        return f'{self.player.user.username} - device {self.id}'
