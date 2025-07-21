from enum import Enum

from django.db import models
from django.utils.translation import gettext_lazy as _


class PlayerEnums(int, Enum):

    DEFAULT_RATING = 1

    LOCATION_MAX_LENGTH = 150
    GENDER_MAX_LENGTH = 6
    LEVEL_MAX_LENGTH = 6


class Genders(models.TextChoices):
    """Gender enums for player."""

    MALE = 'MALE', _('Male')
    FEMALE = 'FEMALE', _('Female')
