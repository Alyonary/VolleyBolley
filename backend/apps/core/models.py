from django.db import models as m
from django.utils.translation import gettext_lazy as _


from apps.core.enums import CoreFieldLength
from apps.core.mixins.name_title import NameMixin, TitleMixin


class Tag(NameMixin):
    """Модель тэга."""

    class Meta:
        verbose_name = _('Тэг')
        verbose_name_plural = _('Тэги')
        default_related_name = 'tags'


class Contact(m.Model):
    """Модель контакта."""
    value = m.CharField(max_length=CoreFieldLength.CONTACT_NAME.value)

    class Meta:
        verbose_name = _('Контакт')
        verbose_name_plural = _('Контакты')
        default_related_name = 'contacts'

    def __str__(self):
        return self.value


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
