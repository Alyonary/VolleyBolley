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


class DailyStats(m.Model):
    """
    Stores aggregated dashboard statistics for a specific date (per day).
    Used to quickly serve dashboard data without heavy DB queries.
    """

    date = m.DateField(unique=True)
    players_registered = m.IntegerField()
    games_created = m.IntegerField()
    tourneys_created = m.IntegerField()

    class Meta:
        verbose_name = _('Daily Stats')
        verbose_name_plural = _('Daily Stats')
        ordering = ['-date']

    def __str__(self):
        return f'Dashboard stats for {self.date}'
