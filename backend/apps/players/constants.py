from enum import Enum, IntEnum

from django.db import models
from django.utils.translation import gettext_lazy as _


class Grades(models.TextChoices):
    """Level enums for players and games."""

    LIGHT = 'LIGHT', _('Beginner')
    MEDIUM = 'MEDIUM', _('Confident amateur')
    HARD = 'HARD', _('Advanced')
    PRO = 'PRO', _('Professional')


class LevelMarkChoices(models.IntegerChoices):
    ONE = 1, '1'
    TWO = 2, '2'
    THREE = 3, '3'


class PlayerIntEnums(IntEnum):

    LOCATION_MAX_LENGTH = 150
    GENDER_MAX_LENGTH = 6
    LEVEL_MAX_LENGTH = 6
    PAYMENT_MAX_LENGTH = 10
    PLAYER_DATA_MAX_LENGTH = 150
    DEFAULT_RATING = 6
    MIN_RATING_VALUE = 0
    MAX_RATING_VALUE = 12





class Genders(models.TextChoices):
    """Gender enums for player."""

    MALE = 'MALE', _('Male')
    FEMALE = 'FEMALE', _('Female')


class PlayerStrEnums(Enum):

    DEFAULT_BIRTHDAY = '2000-01-01'
    DEFAULT_GENDER = Genders.MALE.value
    DEFAULT_GRADE = Grades.LIGHT.value
    DEFAULT_FIRST_NAME = 'Anonym'
    DEFAULT_LAST_NAME = 'Anonym'

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
