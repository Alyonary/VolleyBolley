from django.core.validators import MaxLengthValidator
from django.db import models as m
from django.utils.translation import gettext_lazy as _

from apps.core.models import Payment
from apps.event.enums import EventFieldLength


class EventMixin(m.Model):
    """Миксин события."""

    message = m.TextField(
        verbose_name=_('Описание'),
        validators=[MaxLengthValidator(EventFieldLength.MESSAGE.value)]
    )
    start_time = m.DateTimeField(
        verbose_name=_('Дата и время начала')
    )
    end_time = m.DateTimeField(
        verbose_name=_('Дата и время окончания')
    )
    court = m.ForeignKey(
        'courts.Court',
        verbose_name=_('Площадка'),
        on_delete=m.CASCADE,
        null=False,
        blank=False,
    )
    gender = m.ForeignKey(
        'core.Gender',
        verbose_name=_('Пол участников'),
        on_delete=m.SET_NULL,
        null=True,
        blank=True,
    )
    player_levels = m.ManyToManyField(
        'core.GameLevel',
        verbose_name=_('Уровень игры участников'),
    )
    max_players = m.PositiveIntegerField(
        verbose_name=_('Максимальное количество игроков'),
    )
    price_per_person = m.DecimalField(
        verbose_name=_('Стоимость с человека'),
        max_digits=8,
        decimal_places=2,
        default=0,
        null=False,
        blank=True,
    )
    payment_type = m.CharField(
        verbose_name=_('Payment type'),
        max_length=EventFieldLength.PAYMENT_VALUE.value,
        choices=Payment.PaymentTypeChoices.choices
    )
    payment_account = m.CharField(
        verbose_name=_('Реквизиты счета'),
        max_length=EventFieldLength.PAYMENT_VALUE.value
    )
    currency_type = m.ForeignKey(
        'core.CurrencyType',
        verbose_name=_('Тип валюты'),
        on_delete=m.CASCADE
    )
    is_private = m.BooleanField(
        verbose_name=_('Приватное событие'),
        default=False,
    )
    is_active = m.BooleanField(
        verbose_name=_('Активно'),
        default=True,
    )

    class Meta:
        abstract = True
        ordering = ('date',)
