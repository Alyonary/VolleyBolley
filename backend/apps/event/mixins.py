from django.core.validators import MaxLengthValidator
from django.db import models as m
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericRelation
from apps.core.constants import GenderChoices
from apps.event.enums import EventIntEnums
from apps.players.constants import Payments


class EventMixin(m.Model):
    """Event mixin."""

    message = m.TextField(
        verbose_name=_('Description'),
        validators=[MaxLengthValidator(EventIntEnums.MESSAGE.value)]
    )
    start_time = m.DateTimeField(
        verbose_name=_('Start date and time')
    )
    end_time = m.DateTimeField(
        verbose_name=_('End date and time')
    )
    court = m.ForeignKey(
        'courts.Court',
        verbose_name=_('Court'),
        on_delete=m.CASCADE,
        null=False,
        blank=False,
    )
    gender = m.CharField(
        verbose_name=_('Gender of players'),
        choices=GenderChoices.choices,
        null=True,
        blank=True
    )
    player_levels = m.ManyToManyField(
        'core.GameLevel',
        verbose_name=_('Game level'),
    )
    max_players = m.PositiveIntegerField(
        verbose_name=_('Maximum of players'),
        blank=True,
        null=False
    )
    price_per_person = m.DecimalField(
        verbose_name=_('Price per person'),
        max_digits=8,
        decimal_places=2,
        default=0,
        null=False,
        blank=True,
    )
    payment_type = m.CharField(
        verbose_name=_('Payment type'),
        max_length=EventIntEnums.PAYMENT_VALUE.value,
        choices=Payments.choices
    )
    payment_account = m.CharField(
        verbose_name=_('Payment account'),
        max_length=EventIntEnums.PAYMENT_VALUE.value
    )
    currency_type = m.ForeignKey(
        'core.CurrencyType',
        verbose_name=_('Currency type'),
        on_delete=m.CASCADE
    )
    is_private = m.BooleanField(
        verbose_name=_('Private event'),
        default=False,
    )
    is_active = m.BooleanField(
        verbose_name=_('Active'),
        default=True,
    )
    event_invites = GenericRelation('event.GameInvitation')

    class Meta:
        abstract = True
        ordering = ('start_time',)
