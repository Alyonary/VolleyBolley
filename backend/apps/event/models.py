from django.conf import settings
from django.core.validators import MaxLengthValidator
from django.db import models as m

from apps.event.enums import EventFieldLength


class Event(m.Model):
    """Модель события."""
    title = m.CharField(
        max_length=EventFieldLength.TITLE.value,
    )
    message = m.TextField(
        validators=[MaxLengthValidator(EventFieldLength.MESSAGE.value)]
    )
    date = m.DateField()
    start_time = m.CharField(
        max_length=EventFieldLength.EVENT_TIME.value,
    )
    end_time = m.CharField(
        max_length=EventFieldLength.EVENT_TIME.value,
    )
    area = m.ForeignKey(
        'Area',  # todo: ждем таблицу площадок, меняем название под нее
        on_delete=m.SET_NULL,
        null=True,
        blank=True,
        related_name='events',
    )
    max_players = m.PositiveIntegerField()
    gender = m.ForeignKey(
        'users.UserGender',
        on_delete=m.SET_NULL,
        null=True,
        blank=True,
        related_name='events',
    )
    player_levels = m.ManyToManyField(
        'users.UserGameLevel',
        related_name='events',
    )
    creator = m.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=m.SET_NULL,
        null=True,
        blank=True,
        related_name='created_events',
    )
    players = m.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='joined_events',
    )
    price_per_person = m.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        null=True,
        blank=True,
    )
    payment_type = m.ForeignKey(
        'users.UserPaymentType',
        on_delete=m.SET_NULL,
        null=True,
        blank=True,
        related_name='events',
    )
    payment_value = m.CharField(
        max_length=EventFieldLength.PAYMENT_VALUE.value,
    )
    is_private = m.BooleanField(default=False)
    created_at = m.DateTimeField(auto_now_add=True)
    updated_at = m.DateTimeField(auto_now=True)
    is_active = m.BooleanField(default=True)

    def __str__(self):
        return self.title[:EventFieldLength.STR_MAX_LEN.value]

    class Meta:
        ordering = ('date',)
        constraints = [
            m.UniqueConstraint(
                fields=['title', 'date', 'area'],
                name='unique_event_title_date_area',
            )
        ]
