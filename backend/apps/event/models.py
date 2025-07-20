from django.conf import settings
from django.db import models as m
from django.utils.translation import gettext_lazy as _

from apps.core.mixins.created_updated import CreatedUpdatedMixin
from apps.event.mixins import EventMixin


class Game(EventMixin, CreatedUpdatedMixin):
    """Модель игры."""
    host = m.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('Организатор'),
        on_delete=m.SET_NULL,
        null=True,
        blank=True,
        related_name='games_host',
    )
    players = m.ManyToManyField(
        settings.AUTH_USER_MODEL,
        verbose_name=_('Игроки'),
        related_name='games_players',
    )

    class Meta:
        verbose_name = _('Игра')
        verbose_name_plural = _('Игры')
        default_related_name = 'games'


class Tourney(EventMixin, CreatedUpdatedMixin):
    """Модель турнира."""

    host = m.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('Организатор'),
        on_delete=m.SET_NULL,
        null=True,
        blank=True,
        related_name='tournaments_host',
    )
    players = m.ManyToManyField(
        settings.AUTH_USER_MODEL,
        verbose_name=_('Игроки'),
        related_name='tournaments_players',
    )
    is_individual = m.BooleanField(
        verbose_name=_('Индивидуальный формат'),
        default=False,
    )
    maximum_teams = m.PositiveIntegerField(
        verbose_name=_('Максимум команд'),
    )

    class Meta:
        verbose_name = _('Турнир')
        verbose_name_plural = _('Турниры')
        default_related_name = 'tournaments'
