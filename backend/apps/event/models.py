from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models as m
from django.utils.translation import gettext_lazy as _

from apps.core.mixins.created_updated import CreatedUpdatedMixin
from apps.event.enums import EventFieldLength
from apps.event.mixins import EventMixin

User = get_user_model()


class GameInvitation(m.Model):
    """Invitation to game model."""

    class StatusTypeChoices(m.TextChoices):
        ACCEPTED = 'ACCEPTED', _('Accepted')
        REJECTED = 'REJECTED', _('Rejected')
        NOT_DECIDED = 'NOT_DECIDED', _('Not decided')

    host = m.ForeignKey(User, on_delete=m.CASCADE, related_name='host')

    invited = m.ForeignKey(User, on_delete=m.CASCADE, related_name='invited')

    game = m.ForeignKey('event.Game', on_delete=m.CASCADE)

    status = m.CharField(
        verbose_name=_('Invitation status'),
        max_length=EventFieldLength.TITLE.value,
        choices=StatusTypeChoices.choices,
        default=StatusTypeChoices.NOT_DECIDED
    )

    class Meta:
        verbose_name = _('Game invitation')
        verbose_name_plural = _('Game invitations')

    def __str__(self):
        discription = str(_(
            f'Invitation in {self.game} for {self.invited}: {self.status}'))
        return discription


class Game(EventMixin, CreatedUpdatedMixin):
    """Game model."""
    host = m.ForeignKey(
        User,
        verbose_name=_('Game organizer'),
        on_delete=m.CASCADE,
        related_name='games_host'
    )
    players = m.ManyToManyField(
        User,
        verbose_name=_('Players'),
        related_name='games_players',
        blank=True
    )

    def __str__(self):
        name = (
            f'{self.id}'
            f'{self.court.location.court_name}, '
            f'{self.message[:15]}, '
            f'time: {self.start_time}'
            f'host: {self.host}, '
        )
        return name[:EventFieldLength.STR_MAX_LEN.value]

    class Meta:
        verbose_name = _('Game')
        verbose_name_plural = _('Games')
        default_related_name = 'games'


class Tourney(EventMixin, CreatedUpdatedMixin):
    """Tourney model."""

    host = m.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('Tourney organizer'),
        on_delete=m.SET_NULL,
        null=True,
        blank=True,
        related_name='tournaments_host',
    )
    players = m.ManyToManyField(
        settings.AUTH_USER_MODEL,
        verbose_name=_('Players'),
        related_name='tournaments_players',
    )
    is_individual = m.BooleanField(
        verbose_name=_('Individual format'),
        default=False,
    )
    maximum_teams = m.PositiveIntegerField(
        verbose_name=_('Maximum of teams'),
    )

    class Meta:
        verbose_name = _('Tourney')
        verbose_name_plural = _('Tourneys')
        default_related_name = 'tournaments'
