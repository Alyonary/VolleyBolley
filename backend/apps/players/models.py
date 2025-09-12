from datetime import date

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.enums import Levels
from apps.locations.models import City, Country
from apps.players.constants import (
    Genders,
    Payments,
    PlayerIntEnums,
    PlayerStrEnums,
)

User = get_user_model()


def validate_birthday(value):
    if value > timezone.now().date():
        raise ValidationError(_('Date of birth cannot be in the future.'))


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
        default=PlayerStrEnums.DEFAULT_GENDER.value
    )
    level = models.CharField(
        verbose_name=_('Level of player'),
        max_length=PlayerIntEnums.LEVEL_MAX_LENGTH.value,
        choices=Levels.choices,
        default=PlayerStrEnums.DEFAULT_LEVEL.value,
    )
    avatar = models.ImageField(
        verbose_name=_('Avatar'),
        upload_to='players/avatars/',
        null=True,
        blank=True,
        default=None,
    )
    rating = models.PositiveIntegerField(
        default=PlayerIntEnums.DEFAULT_RATING.value,
        verbose_name=_('Rating of player'),
    )
    date_of_birth = models.DateField(
        default=PlayerStrEnums.DEFAULT_BIRTHDAY.value,
        validators=[validate_birthday],
    )
    country = models.ForeignKey(
        Country,
        related_name='players',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Country of player')
    )
    city = models.ForeignKey(
        City,
        related_name='players',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('City of player')
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

    def clean(self):
        super().clean()
        if self.date_of_birth:
            if not isinstance(self.date_of_birth, date):
                raise ValidationError(
                    {'date_of_birth': _('Invalid date format.')}
                )
            if self.date_of_birth > timezone.now().date():
                raise ValidationError(
                    {'date_of_birth': _('Birthday cannot be in the future')}
                )


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
        null=True,
        blank=True
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
