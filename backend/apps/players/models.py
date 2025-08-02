from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.enums import Levels
from apps.players.constants import (
    Genders,
    Payments,
    PlayerIntEnums,
    PlayerStrEnums,
)

User = get_user_model()


class PlayerLocation(models.Model):
    """Players location model."""

    country = models.CharField(
        _('Country'), max_length=PlayerIntEnums.LOCATION_MAX_LENGTH.value
    )
    city = models.CharField(
        _('City'), max_length=PlayerIntEnums.LOCATION_MAX_LENGTH.value
    )

    class Meta:
        verbose_name = _('Location')
        verbose_name_plural = _('Locations')

    def __str__(self):
        return f"{self.city}, {self.country}"


class Player(models.Model):
    """Player model."""

    user = models.OneToOneField(
        User,
        related_name='player',
        verbose_name=_('User tied to player'),
        on_delete=models.CASCADE,
        null=False,
        blank=False,
    )
    gender = models.CharField(
        verbose_name=_('Gender'),
        max_length=PlayerIntEnums.GENDER_MAX_LENGTH.value,
        choices=Genders.choices,
        blank=False,
        default=Genders.MALE.value
    )
    level = models.CharField(
        verbose_name=_('Level of player'),
        max_length=PlayerIntEnums.LEVEL_MAX_LENGTH.value,
        choices=Levels.choices,
        default=Levels.LIGHT.value,
    )
    avatar = models.ImageField(
        verbose_name=_('Avatar'),
        upload_to='players/avatars/',
        null=True,
        blank=True,
        default=None,
    )
    location = models.ForeignKey(
        PlayerLocation,
        related_name='players',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('Location of player'),
    )
    rating = models.PositiveIntegerField(
        default=PlayerIntEnums.DEFAULT_RATING.value,
        verbose_name=_('Rating of player'),
    )
    date_of_birth = models.DateField(
        default=PlayerStrEnums.DEFAULT_BIRTHDAY.value
    )
    is_registered = models.BooleanField(
        verbose_name=_('Status of player registration in app'),
        default=False,
        null=False
    )

    class Meta:
        verbose_name = _('Player')
        verbose_name_plural = _('Players')

    def __str__(self):
        return f"Player {self.user.first_name} {self.user.last_name}"


class Payment(models.Model):
    """Players payment model."""

    player = models.ForeignKey(
        Player,
        related_name='payments',
        verbose_name=_('Player - owner of payment'),
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        
    )
    payment_type = models.CharField(
        verbose_name=_('Type of payment'),
        max_length=PlayerIntEnums.PAYMENT_MAX_LENGTH.value,
        choices=Payments.choices,
        blank=False
    )
    payment_account = models.CharField(
        verbose_name=_('Payment account of player'),
        max_length=PlayerIntEnums.PAYMENT_MAX_LENGTH.value,
        default=None,
    )
    is_preferred = models.BooleanField(
        verbose_name=_('Players preferable payment type'),
        null=False,
        blank=False,
        default=False
    )

    def __str__(self) -> str:
        return f'Payment data of {self.player}, type: {self.payment_type}'


class Favorite(models.Model):
    """Model of favorite players."""

    player = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        related_name='player',
        verbose_name=_('Player')
    )
    favorite = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        related_name='favorite',
        verbose_name=_('Players favorite')
    )

    class Meta:
        ordering = ['id']
        constraints = [
            models.UniqueConstraint(
                fields=['player', 'favorite'],
                name='unique_player_favorite'
            )
        ]
        verbose_name = _('Favorite')
        verbose_name_plural = _('Favorites')

    def __str__(self) -> str:
        return f'{self.player} has {self.favorite} in favorite list'
