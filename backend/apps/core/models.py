from django.db import models as m
from django.utils.translation import gettext_lazy as _

from apps.core.enums import CoreFieldLength
from apps.core.mixins.name_title import NameMixin, TitleMixin


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


class PaymentType(NameMixin):
    """Модель типа оплаты."""

    class Meta:
        verbose_name = _('Тип оплаты')
        verbose_name_plural = _('Типы оплаты')
        default_related_name = 'payment_types'


class Gender(m.Model):
    """Модель гендера."""

    class GenderChoices(m.TextChoices):
        MIX = 'mix', _('Смешанный')
        MEN = 'men', _('Мужской')
        WOMEN = 'women', _('Женский')

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
        LIGHT = 'light', _('Новичок')
        MEDIUM = 'medium', _('Средний')
        HARD = 'hard', _('Продвинутый')
        PRO = 'pro', _('Профессионал')

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
