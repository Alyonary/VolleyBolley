from django.db import models
from django.utils.translation import gettext_lazy as _


class Country(models.Model):
    '''Country model.'''

    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_('Country name'),
        default='',
        help_text=_('Name of the country')
    )

    class Meta:
        verbose_name = _('Country')
        verbose_name_plural = _('Countries')
        ordering = ['name']

    def __str__(self):
        return self.name


class City(models.Model):
    '''City model.'''

    name = models.CharField(
        max_length=100,
        verbose_name=_('City name'),
        default='',
        help_text=_('Name of the city')
    )
    country = models.ForeignKey(
        Country,
        on_delete=models.CASCADE,
        related_name='cities',
        verbose_name=_('Country')
    )

    class Meta:
        verbose_name = _('City')
        verbose_name_plural = _('Cities')
        ordering = ['country__name', 'name']
        unique_together = ['name', 'country']

    def __str__(self):
        return f'{self.name}, {self.country.name}'
