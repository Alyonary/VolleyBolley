from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.notifications.constants import (
    DEVICE_PLATFORM_LENGTH,
    DEVICE_TOKEN_MAX_LENGTH,
    NOTIFICATION_INIT_DATA,
    NOTIFICATION_SCREEN_MAX_LENGTH,
    NOTIFICATION_TITLE_MAX_LENGTH,
    NOTIFICATION_TYPE_MAX_LENGTH,
    DeviceType,
    NotificationTypes,
)


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

    def in_tourney(self, tourney_id):
        """
        Return devices for all players participating in a specific tourney.
        """
        return self.active().filter(player__tournaments_players=tourney_id)

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

    def in_tourney(self, tourney_id):
        """Return devices for all players in a specific tourney."""
        return self.get_queryset().in_tourney(tourney_id)

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
        max_length=DEVICE_PLATFORM_LENGTH,
        choices=DeviceType.choices,
        default=DeviceType.ANDROID
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


class NotificationsBase(models.Model):
    """Model for defining different types of notifications."""
    type = models.CharField(
        max_length=NOTIFICATION_TYPE_MAX_LENGTH,
        choices=NotificationTypes.CHOICES,
        unique=True,
        db_index=True
    )
    title = models.CharField(
        max_length=NOTIFICATION_TITLE_MAX_LENGTH,
        null=False,
        blank=False
    )
    body = models.TextField(
        null=False,
        blank=False
    )
    screen = models.CharField(
        max_length=NOTIFICATION_SCREEN_MAX_LENGTH,
        null=False,
        blank=False
    )

    class Meta:
        verbose_name = _('Notification Type')
        verbose_name_plural = _('Notification Types')
        indexes = [
            models.Index(fields=['type']),
        ]

    def __str__(self):
        return f'Notification Type: {self.type}'

    @classmethod
    def create_db_model_types(cls):
        """
        Create initial notification types in the database.
        This method checks if the notification types defined in
        NOTIFICATION_INIT_DATA exist, and creates them if they do not.
        """

        for notif_type, data in NOTIFICATION_INIT_DATA.items():
            cls.objects.get_or_create(
                type=notif_type,
                defaults={
                    'title': data['title'],
                    'body': data['body'],
                    'screen': data['screen'],
                }
            )


class Notifications(models.Model):
    """Model for storing notification messages."""

    player = models.ForeignKey(
        'players.Player',
        related_name='notifications',
        on_delete=models.CASCADE,
        verbose_name=_('Player'),

    )
    notification_type = models.ForeignKey(
        'notifications.NotificationsBase',
        on_delete=models.CASCADE,
        verbose_name=_('Notification type'),
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
    tourney = models.ForeignKey(
        'event.Tourney',
        related_name='notifications',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('Related tourney'),
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
        return (
            f'Notification {self.notification_type} '
            f'for {self.player.user.username}'
        )
