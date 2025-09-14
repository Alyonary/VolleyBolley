from enum import Enum

from django.db import models
from django.utils.translation import gettext_lazy as _


class CoreFieldLength(int, Enum):
    """Constants for Core app."""

    NAME = 70
    NAME_STR = 30
    TITLE = 50
    TITLE_STR = 30
    CONTACT_NAME = 255
    ADMIN_LIST_PER_PAGE = 25
    ADMIN_INFO_SHORT_CONTENT = 50


class Levels(models.TextChoices):
    """Level enums for players and games."""

    LIGHT = 'LIGHT', _('Beginner')
    MEDIUM = 'MEDIUM', _('Confident amateur')
    HARD = 'HARD', _('Advanced')
    PRO = 'PRO', _('Professional')
