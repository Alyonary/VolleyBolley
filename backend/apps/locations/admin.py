from django.contrib import admin

from apps.locations.models import City, Country


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    """Admin configuration for Country model."""

    list_display = ['name']
    search_fields = ['name']
    ordering = ['name']


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    """Admin configuration for City model."""

    list_display = ['name', 'country']
    list_filter = ['country']
    search_fields = ['name', 'country__name']
    ordering = ['country__name', 'name']

    fieldsets = (('City Information', {'fields': ('name', 'country')}),)
