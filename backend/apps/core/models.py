from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import models as m
from django.utils.translation import gettext_lazy as _

from apps.core.enums import CoreFieldLength
from apps.core.mixins.name_title import NameMixin, TitleMixin
from apps.locations.models import Country

User = get_user_model()


class Tag(NameMixin):
    """Tag model."""

    class Meta:
        verbose_name = _('Tag')
        verbose_name_plural = _('Tags')
        default_related_name = 'tags'


class Contact(m.Model):
    """Contact model."""

    contact_type = m.CharField(
        _('Contact type'),
        max_length=CoreFieldLength.CONTACT_NAME.value,
        null=False,
        blank=False,
        default='PHONE',
    )
    contact = m.CharField(
        _('Contact value'),
        max_length=CoreFieldLength.CONTACT_NAME.value,
        null=True,
        blank=True,
        default=None,
    )
    court = m.ForeignKey('courts.Court', on_delete=m.CASCADE)

    class Meta:
        verbose_name = _('Contact')
        verbose_name_plural = _('Contacts')
        default_related_name = 'contacts'

    def __str__(self):
        return f'{self.contact_type} {self.contact}'


class GameLevel(m.Model):
    """Game level model."""

    class GameLevelChoices(m.TextChoices):
        """Game levels enum for game."""

        LIGHT = 'LIGHT', _('Beginner')
        MEDIUM = 'MEDIUM', _('Intermediate')
        HARD = 'HARD', _('Advanced')
        PRO = 'PRO', _('Professional')

    name = m.CharField(
        verbose_name=_('Game level'),
        max_length=CoreFieldLength.NAME.value,
        choices=GameLevelChoices.choices,
        unique=True,
    )

    def __str__(self):
        return self.get_name_display()

    class Meta:
        verbose_name = _('Game level')
        verbose_name_plural = _('Game levels')
        default_related_name = 'game_levels'
        ordering = ('name',)


class InfoPage(TitleMixin):
    """Information page (FAQ, rules, contacts, etc.)."""

    tag = m.ForeignKey(
        Tag,
        verbose_name=_('Tag'),
        on_delete=m.CASCADE,
        related_name='info_pages',
    )

    class Meta(TitleMixin.Meta):
        verbose_name = _('Info page')
        verbose_name_plural = _('Info pages')
        default_related_name = 'info_pages'


class InfoSection(TitleMixin):
    """Section of the information page."""

    page = m.ForeignKey(
        InfoPage,
        verbose_name=_('Page'),
        on_delete=m.CASCADE,
        related_name='sections',
    )
    content = m.TextField(
        verbose_name=_('Content'),
    )
    order = m.PositiveIntegerField(verbose_name=_('Ordering'), default=0)

    class Meta(TitleMixin.Meta):
        verbose_name = _('Section of the information page')
        verbose_name_plural = _('Sections of the information page')
        default_related_name = 'sections'
        ordering = ('page', 'order')


class CurrencyType(m.Model):
    """Currency type model."""

    class CurrencyTypeChoices(m.TextChoices):
        EUR = 'EUR', _('Euro')
        THB = 'THB', _('THB')

    class CurrencyNameChoices(m.TextChoices):
        EUR = '€', _('Euro')
        THB = '฿', _('THB')

    currency_type = m.CharField(
        verbose_name=_('Currency type'),
        max_length=CoreFieldLength.NAME.value,
        choices=CurrencyTypeChoices.choices,
        unique=True,
    )

    currency_name = m.CharField(
        verbose_name=_('Currency label'),
        max_length=CoreFieldLength.NAME.value,
        choices=CurrencyNameChoices.choices,
        unique=True,
    )
    country = m.ForeignKey(
        Country, on_delete=m.SET_NULL, null=True, blank=True
    )

    def __str__(self):
        return self.currency_type

    class Meta:
        verbose_name = _('Currency type')
        verbose_name_plural = _('Currency types')
        default_related_name = 'currency_types'


class FAQ(m.Model):
    """FAQ model to store project description."""

    name = m.CharField(
        max_length=CoreFieldLength.NAME.value,
        unique=True,
        default='',
    )
    is_active = m.BooleanField(default=False)
    created_at = m.DateTimeField(auto_now_add=True)
    updated_at = m.DateTimeField(auto_now=True)
    content = m.TextField()

    class Meta:
        verbose_name = _('FAQ')
        verbose_name_plural = _('FAQs')

    def __str__(self):
        return f'FAQ (ID: {self.id}, Active: {self.is_active})'

    def save(self, *args, **kwargs):
        if not self.name:
            super().save(*args, **kwargs)
            self.name = f'faq {self.id}'
            return super().save(update_fields=['name'])
        return super().save(*args, **kwargs)

    @classmethod
    def get_active(cls):
        """Get the active FAQ instance."""
        return cls.objects.filter(is_active=True).first()


class NotificationsTime(m.Model):
    """Notification time model."""

    name = m.CharField(
        max_length=CoreFieldLength.NAME.value,
        unique=True,
        default='Develop Notifications Time Settings',
    )
    closed_event_notification = m.DurationField(
        verbose_name=_('Notifications time after events are closed'),
        default=timedelta(hours=1),
    )
    pre_event_notification = m.DurationField(
        verbose_name=_('Notifications time before events start'),
        default=timedelta(hours=1),
    )
    advance_notification = m.DurationField(
        verbose_name=_('Notifications time in advance of the event'),
        default=timedelta(hours=24),
    )
    is_active = m.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Notifications time settings')
        verbose_name_plural = _('Notification times')
        default_related_name = 'notification_times'

    @classmethod
    def get_active(cls) -> 'NotificationsTime':
        """Get the active NotificationsTime instance."""
        return cls.objects.filter(is_active=True).first()

    @classmethod
    def get_pre_event_time(cls) -> timedelta:
        """Get the pre-event notification time."""
        return cls.get_active().pre_event_notification

    @classmethod
    def get_closed_event_notification_time(cls) -> timedelta:
        """Get the active NotificationsTime instance."""
        return cls.get_active().closed_event_notification

    @classmethod
    def get_advance_notification_time(cls) -> timedelta:
        """Get advance notification time."""
        return cls.get_active().advance_notification
