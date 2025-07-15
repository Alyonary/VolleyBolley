from django.db import models as m
from django.utils.translation import gettext_lazy as _


class CreatedUpdatedMixin(m.Model):
    """Миксин с полями времени создания и изменения."""

    created_at = m.DateTimeField(
        verbose_name=_('Дата создания'),
        auto_now_add=True,
        db_index=True,
    )
    updated_at = m.DateTimeField(
        verbose_name=_('Дата обновления'),
        auto_now=True,
    )

    class Meta:
        abstract = True
