from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.event.models import Game
from apps.notifications.constants import DEVICE_TOKEN_MAX_LENGTH, DeviceType
from apps.players.models import Player


class DeviceManager(models.Manager):
    """Custom manager for Device model."""

    def active(self):
        """Return only active devices."""
        return self.get_queryset().filter(is_active=True)

    def in_game(self, game_id):
        """Return devices associated with players in a specific game."""
        game = Game.objects.filter(id=game_id).first()
        user_ids = game.players.values_list('id', flat=True)
        player_ids = Player.objects.filter(
            user_id__in=user_ids
        ).values_list('id', flat=True)
        return self.active().filter(player_id__in=player_ids)

    def by_player(self, player_id):
        """Return devices associated with a specific player."""
        return self.active(
            ).filter(player_id=player_id)

    def update_or_create_token(
        self,
        token,
        player,
        platform=None,
        is_active=True
    ):
        """
        Update or create a device with the given token and player.
        If a device with the token already exists, it updates the player
        and active status. If it doesn't exist, it creates a new device.
        Returns the device and a boolean indicating if it was created.
        """
        if not platform:
            platform = DeviceType.ANDROID
        try:
            device = self.get(token=token)
            device.player = player
            device.platform = platform
            device.is_active = is_active
            device.save()
            return device, False
        except self.model.DoesNotExist:
            device = self.create(
                token=token,
                player=player,
                platform=platform,
                is_active=is_active
            )
            return device, True


class Device(models.Model):
    """Model for storing device information for push notifications."""
    token = models.CharField(
        max_length=DEVICE_TOKEN_MAX_LENGTH,
        unique=True
    )
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
