from django.core.validators import MaxLengthValidator
from django.db import models as m
from django.utils.translation import gettext_lazy as _

from apps.event.enums import EventFieldLength


class EventMixin(m.Model):
    """Миксин события."""

    message = m.TextField(
        verbose_name=_('Описание'),
        validators=[MaxLengthValidator(EventFieldLength.MESSAGE.value)]
    )
    date = m.DateTimeField(
        verbose_name=_('Дата и время')
    )
    start_time = m.TimeField(
        verbose_name=_('Время начала')
    )
    end_time = m.TimeField(
        verbose_name=_('Время окончания')
    )
    court = m.ForeignKey(
        'courts.Court',
        verbose_name=_('Площадка'),
        on_delete=m.SET_NULL,
        null=True,
        blank=True,
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
    # ##### Надо подумать как тут сделать.
    # У нас модель Payment содержит это поле.
    # В каком виде ее сюда тянуть?
    payment_type = m.ForeignKey(
        'core.Payment',
        verbose_name=_('Тип оплаты'),
        on_delete=m.SET_NULL,
        null=True,
        blank=True,
    )
    payment_value = m.CharField(
        verbose_name=_('Описание оплаты'),
        max_length=EventFieldLength.PAYMENT_VALUE.value,
    )
    is_private = m.BooleanField(
        verbose_name=_('Приватное событие'),
        default=False,
    )
    is_active = m.BooleanField(
        verbose_name=_('Активно'),
        default=True,
    )

    def __str__(self):
        return self.title[:EventFieldLength.STR_MAX_LEN.value]

    class Meta:
        abstract = True
        ordering = ('date',)
