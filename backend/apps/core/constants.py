import re

from django.db import models as m
from django.utils.translation import gettext_lazy as _


class GenderChoices(m.TextChoices):
    """Gender enums for game."""

    MIX = 'MIX', _('Mixed')
    MEN = 'MEN', _('Men')
    WOMEN = 'WOMEN', _('Women')


DEFAULT_FAQ: str = 'default_faq'


class ContactTypes(m.TextChoices):
    """Contact type enums for contact model."""

    PHONE = 'PHONE', _('Phone')
    EMAIL = 'EMAIL', _('Email')
    WEBSITE = 'WEBSITE', _('Website')


DOMAIN_REGEX = re.compile(r'^(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}$')
