from django.db import models as m
from django.utils.translation import gettext_lazy as _

from apps.core.enums import CoreFieldLength


class NameMixin(m.Model):
    """Mixin with 'name' field."""

    name = m.CharField(
        max_length=CoreFieldLength.NAME.value,
        unique=True,
    )

    class Meta:
        abstract = True
        ordering = ('name',)

    def __str__(self):
        return self.name[:CoreFieldLength.NAME_STR.value]


class TitleMixin(m.Model):
    """Mixin with 'title' field."""

    title = m.CharField(
        verbose_name=_('Заголовок'),
        max_length=CoreFieldLength.TITLE.value,
    )

    class Meta:
        abstract = True
        ordering = ('title',)

    def __str__(self):
        return self.title[:CoreFieldLength.TITLE_STR.value]
