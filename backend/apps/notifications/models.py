from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.event.models import Game
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
            ).filter(player_id=player_id).values_list('token', flat=True)


class DeviceType(models.TextChoices):
    IOS = 'ios', 'ios'
    ANDROID = 'android', 'android'
    WEB = 'web', 'web'


class Device(models.Model):
    '''Model for storing device information for push notifications.'''
    token = models.CharField(max_length=255, unique=True)
    # device_type = models.CharField(
    #     max_length=10,
    #     choices=DeviceType.choices,
    #     default=DeviceType.ANDROID
    # )
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
        return f'{self.player.user.username} - {self.device_type}'
