from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Court, Location


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'longitude',
        'latitude',
        'court_name',
        'location_name')
    search_fields = ('court_name', 'location_name')
    list_filter = ('location_name',)
    empty_value_display = _('Not defined')
    list_display_links = ('id', 'location_name')


@admin.register(Court)
class CourtAdmin(admin.ModelAdmin):
    list_display = (
        'location',
        'court_name',
        'price_description',
        'description',
        'photo_url',
        'working_hours',
        'is_active'
    )
    fields = (
        'location',
        'court_name',
        'price_description',
        'description',
        'contacts_list',
        'photo_url',
        'tag_list',
        'working_hours',
        'is_active'
    )
    search_fields = ('court_name',)
    list_display_links = ('location',)
    empty_value_display = _('Not defined')
    filter_horizontal = ('tag_list', 'contacts_list')

    def court_name(self, obj):
        return obj.location.court_name
    court_name.short_description = _('Court name')
