from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import Tag
from apps.courts.enums import CourtEnums, LocationEnums
from apps.locations.models import City, Country


class CourtLocation(models.Model):
    '''Court location model.'''

    longitude = models.FloatField(
        _('Longtitude'),
        validators=(
            MinValueValidator(
                LocationEnums.MIN_LONGTITUDE.value,
                message=_(
                    f'Min longtitude: {LocationEnums.MIN_LONGTITUDE.value}')),
            MaxValueValidator(
                LocationEnums.MAX_LONGTITUDE.value,
                message=_(
                    f'Max longtitude: {LocationEnums.MAX_LONGTITUDE.value}')),
        )
    )

    latitude = models.FloatField(
        _('latitude'),
        validators=(
            MinValueValidator(
                LocationEnums.MIN_LATITUDE.value,
                message=_(
                    f'Min latitude: {LocationEnums.MIN_LATITUDE.value}')),
            MaxValueValidator(
                LocationEnums.MAX_LATITUDE.value,
                message=_(
                    f'Max latitude: {LocationEnums.MAX_LATITUDE.value}')),
        )
    )
    court_name = models.CharField(
        _('Court name'),
        max_length=LocationEnums.LOCATION_NAME_LENGTH.value
    )
    country = models.ForeignKey(
        Country,
        verbose_name=_('Country'),
        on_delete=models.SET_NULL,
        null=True
    )
    city = models.ForeignKey(
        City,
        verbose_name=_('City'),
        on_delete=models.SET_NULL,
        null=True
    )

    class Meta:
        verbose_name = _('Location')
        verbose_name_plural = _('Locations')
        default_related_name = 'locations'
        ordering = ('-court_name',)

    @property
    def location_name(self):
        if self.country and self.city.name:
            return f'{self.country.name}, {self.city.name}'
        return None

    def __str__(self):
        return self.court_name


class Court(models.Model):
    '''Court model.'''
    location = models.ForeignKey(
        CourtLocation, on_delete=models.CASCADE
    )
    price_description = models.TextField(
        _('Price'),
        blank=True,
    )
    description = models.TextField(
        _('Description'),
        blank=True
    )

    photo_url = models.ImageField(
        upload_to='courts/images/',
        null=True,
        blank=True
    )
    tag_list = models.ManyToManyField(
        Tag,
        blank=True,
    )
    working_hours = models.CharField(
        _('Working hours'),
        max_length=CourtEnums.WORKING_HOURS_LENGTH.value,
        blank=True
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = _('Court')
        verbose_name_plural = _('Courts')
        default_related_name = 'courts'

    def __str__(self):
        return self.location.court_name
