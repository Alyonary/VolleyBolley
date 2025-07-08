from django.db import models

from apps.location.enums import LocationFieldLength


class NameMixin(models.Model):
    name = models.CharField(
        max_length=LocationFieldLength.NAME.value,
        unique=True,
    )

    class Meta:
        abstract = True
