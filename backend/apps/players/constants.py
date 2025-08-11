from enum import Enum, IntEnum

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.enums import Levels


class PlayerIntEnums(IntEnum):

    DEFAULT_RATING = 1

    LOCATION_MAX_LENGTH = 150
    GENDER_MAX_LENGTH = 6
    LEVEL_MAX_LENGTH = 6
    PAYMENT_MAX_LENGTH = 10
    PLAYER_DATA_MAX_LENGTH = 150

class Genders(models.TextChoices):
    """Gender enums for player."""

    MALE = 'MALE', _('Male')
    FEMALE = 'FEMALE', _('Female')


class PlayerStrEnums(Enum):
    
    DEFAULT_BIRTHDAY = '2000-01-01'
    DEFAULT_GENDER = Genders.MALE.value
    DEFAULT_LEVEL = Levels.LIGHT.value


class Payments(models.TextChoices):
    """Payments types."""

    REVOLUT = 'REVOLUT', _('Revolut')
    THAIBANK = 'THAIBANK', _('Thai bank')
    CASH = 'CASH', _('Cash')


BASE_PAYMENT_DATA = [
    {
        'payment_type': Payments.CASH,
        'payment_account': None,
        'is_preferred': True
    },
    {
        'payment_type': Payments.REVOLUT,
        'payment_account': None,
        'is_preferred': False
    },
    {
        'payment_type': Payments.THAIBANK,
        'payment_account': None,
        'is_preferred': False
    },
]