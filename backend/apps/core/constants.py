from django.db import models as m
from django.utils.translation import gettext_lazy as _


class GenderChoices(m.TextChoices):
    """Gender enums for game."""
    MIX = 'MIX', _('Mixed')
    MEN = 'MEN', _('Men')
    WOMEN = 'WOMEN', _('Women')

DEFAULT_FAQ: str = 'default_faq'