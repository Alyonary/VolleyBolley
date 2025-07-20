from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from .constants import (
    MAX_LATITUDE,
    MAX_LONGTITUDE,
    MIN_LATITUDE,
    MIN_LONGTITUDE,
)


class Location(models.Model):
    '''Модель локации.'''

    longitude = models.FloatField(
        _('Долгота'),
        validators=(
            MinValueValidator(
                MIN_LONGTITUDE,
                message=_(f'Минимальная долгота: {MIN_LONGTITUDE}')),
            MaxValueValidator(
                MAX_LONGTITUDE,
                message=_(f'Максимальная долгота: {MIN_LONGTITUDE}')),
        )
    )

    latitude = models.FloatField(
        _('Широта'),
        validators=(
            MinValueValidator(
                MIN_LATITUDE,
                message=_(f'Минимальная широта: {MIN_LATITUDE}')),
            MaxValueValidator(
                MAX_LATITUDE,
                message=_(f'Максимальная широта: {MAX_LATITUDE}')),
        )
    )
    court_name = models.CharField(
        _('Название корта'),
        max_length=100
    )
    name = models.CharField(
        _('Название локации'),
        max_length=255
    )

    class Meta:
        verbose_name = _('Локация')
        verbose_name_plural = _('Локации')
        default_related_name = 'locations'
        ordering = ('-name',)

    def __str__(self):
        return self.court_name


class Court(models.Model):
    '''Модель корта.'''
    location = models.ForeignKey(
        Location, on_delete=models.CASCADE
    )
    price_description = models.TextField(
        _('Стоимость'),
        blank=True,
    )
    description = models.TextField(
        _('Описание'),
        blank=True
    )
    contacts_list = models.ManyToManyField(
        'core.Contact',
        blank=True
    )
    photo_url = models.ImageField(
        upload_to='courts/images/',
        null=True,
        blank=True
    )
    tag_list = models.ManyToManyField(
        'core.Tag',
        blank=True,
    )
    working_hours = models.CharField(
        _('Часы работы'),
        max_length=255,
        blank=True
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = _('Корт')
        verbose_name_plural = _('Корты')
        default_related_name = 'courts'

    def __str__(self):
        return self.location.court_name
