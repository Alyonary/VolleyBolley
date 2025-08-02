from enum import Enum, IntEnum

from django.db import models
from django.utils.translation import gettext_lazy as _


class PlayerIntEnums(IntEnum):

    DEFAULT_RATING = 1

    LOCATION_MAX_LENGTH = 150
    GENDER_MAX_LENGTH = 6
    LEVEL_MAX_LENGTH = 6
    PAYMENT_MAX_LENGTH = 10


class PlayerStrEnums(Enum):
    
    DEFAULT_BIRTHDAY = '2000-01-01'
    

class Genders(models.TextChoices):
    """Gender enums for player."""

    MALE = 'MALE', _('Male')
    FEMALE = 'FEMALE', _('Female')


class Payments(models.TextChoices):
    """Payments types."""

    REVOLUT = 'REVOLUT', _('Revolut')
    THAIBANK = 'THAIBANK', _('Thai bank')
    CASH = 'CASH', _('Cash')


class LocationEnums(str, Enum):

    DEFAULT_COUNTRY = 'Cyprus'
    DEFAULT_CITY = 'Nicosia'


BASE_PAYMENT_DATA = [
    {
        'payment_type': Payments.CASH.value,
        'payment_account': None,
        'is_preferred': True
    },
    {
        'payment_type': Payments.REVOLUT,
        'payment_account': None,
        'is_preferred': False
    },
    {
        'payment_type': Payments.THAIBANK.value,
        'payment_account': None,
        'is_preferred': False
    },
]