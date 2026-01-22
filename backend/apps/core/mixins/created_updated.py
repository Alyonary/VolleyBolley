from django.db import models as m
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class CreatedUpdatedMixin(m.Model):
    """Mixin with creation and updating time fields."""

    created_at = m.DateTimeField(
        verbose_name=_('Created at'),
        default=timezone.now,
        db_index=True,
    )
    updated_at = m.DateTimeField(
        verbose_name=_('Updated at'),
        auto_now=True,
    )

    class Meta:
        abstract = True
