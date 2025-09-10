from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.notifications.constants import (
    DEVICE_TOKEN_MAX_LENGTH,
    NOTIFICATION_TYPE_MAX_LENGTH,
    DeviceType,
)
from apps.notifications.notifications import NotificationTypes


class DeviceQuerySet(models.QuerySet):
    """
    Custom QuerySet for Device model.
    Allows chaining custom filters and queries.
    """

    def active(self):
        """Return only active devices."""
        return self.filter(is_active=True)

    def in_game(self, game_id):
        """
        Return devices for all players participating in a specific game.
        """
        return self.active().filter(player__games_players=game_id)

    def by_player(self, player_id):
        """Return active devices for a specific player."""
        return self.active().filter(player_id=player_id)


class DeviceManager(models.Manager):
    """
    Custom manager for Device model.
    Uses DeviceQuerySet for advanced querying.
    """

    def get_queryset(self):
        return DeviceQuerySet(self.model, using=self._db)

    def active(self):
        """Return only active devices."""
        return self.get_queryset().active()

    def in_game(self, game_id):
        """Return devices for all players in a specific game."""
        return self.get_queryset().in_game(game_id)

    def by_player(self, player_id):
        """Return active devices for a specific player."""
        return self.get_queryset().by_player(player_id)

    def update_or_create_token(
        self, token, player, platform=None, is_active=True
    ):
        """
        Update or create a device with the given token and player.
        If a device with the token already exists, it updates the player
        and active status. If it doesn't exist, it creates a new device.
        Returns the device and a boolean indicating if it was created.
        """
        if not platform:
            platform = DeviceType.ANDROID
        device, created = self.update_or_create(
            token=token,
            defaults={
                'player': player,
                'platform': platform,
                'is_active': is_active,
            },
        )
        return device, created


class Device(models.Model):
    """Model for storing device information for push notifications."""

    token = models.CharField(max_length=DEVICE_TOKEN_MAX_LENGTH, unique=True)
    platform = models.CharField(
        max_length=10, choices=DeviceType.choices, default=DeviceType.ANDROID
    )
    player = models.ForeignKey(
        'players.Player', related_name='devices', on_delete=models.CASCADE
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


class Notifications(models.Model):
    """Model for storing notification messages."""

    player = models.ForeignKey(
        'players.Player',
        related_name='notifications',
        on_delete=models.CASCADE,
    )
    type = models.CharField(
        max_length=NOTIFICATION_TYPE_MAX_LENGTH,
        verbose_name=_('Notification type'),
        choices=NotificationTypes.CHOICES,
    )
    is_read = models.BooleanField(default=False, verbose_name=_('Is read'))
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_('Created at')
    )
    game = models.ForeignKey(
        'event.Game',
        related_name='notifications',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('Related game'),
    )

    class Meta:
        verbose_name = _('Notification')
        verbose_name_plural = _('Notifications')
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        """Ensure is_read is False on creation."""
        if self._state.adding:
            self.is_read = False
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Notification {self.type} for {self.player.user.username}'
