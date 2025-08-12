from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.enums import Levels
from apps.players.enums import Genders, PlayerEnums

User = get_user_model()


class PlayerLocation(models.Model):
    """Players location model."""

    country = models.CharField(
        _('Country'), max_length=PlayerEnums.LOCATION_MAX_LENGTH.value
    )
    city = models.CharField(
        _('City'), max_length=PlayerEnums.LOCATION_MAX_LENGTH.value
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
        max_length=PlayerEnums.GENDER_MAX_LENGTH.value,
        choices=Genders.choices,
        blank=False,
        default=Genders.MALE
    )
    level = models.CharField(
        verbose_name=_('Level of player'),
        max_length=PlayerEnums.LEVEL_MAX_LENGTH.value,
        choices=Levels.choices,
        default=Levels.LIGHT,
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
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('Location of player'),
    )
    rating = models.PositiveIntegerField(
        default=PlayerEnums.DEFAULT_RATING.value,
        verbose_name=_('Rating of player'),
    )

    class Meta:
        verbose_name = _('Player')
        verbose_name_plural = _('Players')
