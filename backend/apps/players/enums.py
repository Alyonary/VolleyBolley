from enum import Enum

from django.db import models
from django.utils.translation import gettext_lazy as _


class PlayerEnum(int, Enum):

    DEFAULT_RATING = 1

    LOCATION_MAX_LENGTH = 150
    GENDER_MAX_LENGTH = 6
    LEVEL_MAX_LENGTH = 6


class Gender(models.TextChoices):
    """Gender enums for player."""

    MALE = 'male', _('Male')
    FEMALE = 'female', _('Female')
