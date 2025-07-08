from django.db import models

from apps.location.enums import LocationFieldLength
from apps.location.mixins import NameMixin


class Country(NameMixin, models.Model):
    """Модель страны."""

    def __str__(self):
        return self.name[:LocationFieldLength.STR_MAX_LEN.value]


class City(NameMixin, models.Model):
    """Модель города."""
    country = models.ForeignKey(
        Country,
        related_name='cities',
        on_delete=models.CASCADE
    )

    def __str__(self):
        return self.name[:LocationFieldLength.STR_MAX_LEN.value]
