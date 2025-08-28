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
        default='PHONE'
    )
    contact = m.CharField(
        _('Contact value'),
        max_length=CoreFieldLength.CONTACT_NAME.value,
        null=True,
        blank=True,
        default=None
    )
    court = m.ForeignKey('courts.Court', on_delete=m.CASCADE)

    class Meta:
        verbose_name = _('Contact')
        verbose_name_plural = _('Contacts')
        default_related_name = 'contacts'

    def __str__(self):
        return f'{self.contact_type} {self.contact}'


class Payment(m.Model):
    """Payment types model."""

    class PaymentTypeChoices(m.TextChoices):
        REVOLUT = 'REVOLUT', _('Revolut')
        THAIBANK = 'THAIBANK', _('Thai bank')
        CASH = 'CASH', _('Cash')

    owner = m.ForeignKey(
        User,
        on_delete=m.CASCADE
    )

    payment_type = m.CharField(
        verbose_name=_('Payment type'),
        max_length=CoreFieldLength.NAME.value,
        choices=PaymentTypeChoices.choices
    )

    payment_account = m.CharField(
        _('Payment account'),
        max_length=CoreFieldLength.NAME.value,
        blank=True,
        null=True
    )

    is_preferred = m.BooleanField(default=False)

    def __str__(self):
        return (f'Payment type: {self.payment_type}, '
                f'for user: {self.owner}')

    class Meta:
        verbose_name = _('Payment type')
        verbose_name_plural = _('Payment types')
        default_related_name = 'payments'


class Gender(m.Model):
    """Модель гендера."""

    class GenderChoices(m.TextChoices):
        MIX = 'MIX', _('Смешанный')
        MEN = 'MEN', _('Мужской')
        WOMEN = 'WOMEN', _('Женский')

    name = m.CharField(
        verbose_name=_('Пол'),
        max_length=CoreFieldLength.NAME.value,
        choices=GenderChoices.choices,
        unique=True,
    )

    def __str__(self):
        return self.get_name_display()

    class Meta:
        verbose_name = _('Пол')
        verbose_name_plural = _('Пола')
        default_related_name = 'genders'
        ordering = ('name',)


class GameLevel(m.Model):
    """Модель игрового уровня."""

    class GameLevelChoices(m.TextChoices):
        LIGHT = 'LIGHT', _('Новичок')
        MEDIUM = 'MEDIUM', _('Средний')
        HARD = 'HARD', _('Продвинутый')
        PRO = 'PRO', _('Профессионал')

    name = m.CharField(
        verbose_name=_('Уровень'),
        max_length=CoreFieldLength.NAME.value,
        choices=GameLevelChoices.choices,
        unique=True,
    )

    def __str__(self):
        return self.get_name_display()

    class Meta:
        verbose_name = _('Уровень игры')
        verbose_name_plural = _('Уровни игры')
        default_related_name = 'game_levels'
        ordering = ('name',)


class InfoPage(TitleMixin):
    """Страница с информацией (FAQ, правила, контакты и т.д.)."""
    tag = m.ForeignKey(
        Tag,
        verbose_name=_('Тег'),
        on_delete=m.CASCADE,
        related_name='info_pages',
    )

    class Meta(TitleMixin.Meta):
        verbose_name = _('Информационная страница')
        verbose_name_plural = _('Информационные страницы')
        default_related_name = 'info_pages'


class InfoSection(TitleMixin):
    """Раздел информационной страницы."""
    page = m.ForeignKey(
        InfoPage,
        verbose_name=_('Страница'),
        on_delete=m.CASCADE,
        related_name='sections',
    )
    content = m.TextField(
        verbose_name=_('Содержимое'),
    )
    order = m.PositiveIntegerField(
        verbose_name=_('Сортировка'),
        default=0
    )

    class Meta(TitleMixin.Meta):
        verbose_name = _('Раздел информационной страницы')
        verbose_name_plural = _('Разделы информационных страниц')
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
        Country,
        on_delete=m.SET_NULL,
        null=True,
        blank=True)

    def __str__(self):
        return self.currency_type

    class Meta:
        verbose_name = _('Currency type')
        verbose_name_plural = _('Currency types')
        default_related_name = 'currency_types'
