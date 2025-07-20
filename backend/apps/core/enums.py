from enum import Enum

from django.db import models
from django.utils.translation import gettext_lazy as _


class CoreFieldLength(int, Enum):
    """Константы для приложения Core."""

    NAME = 70
    NAME_STR = 30
    TITLE = 50
    TITLE_STR = 30
    CONTACT_NAME = 255
    ADMIN_LIST_PER_PAGE = 25
    ADMIN_INFO_SHORT_CONTENT = 50


class Level(models.TextChoices):
    """Level enums for players and games."""

    LIGHT = 'light', _('Beginner')
    MEDIUM = 'medium', _('Confident amateur')
    HARD = 'hard', _('Advanced')
    PRO = 'pro', _('Professional')
