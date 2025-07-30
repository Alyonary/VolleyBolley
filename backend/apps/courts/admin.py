from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import Court, CourtLocation


@admin.register(CourtLocation)
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
        'loc_court_name',
        'link_to_location',
        'price_description',
        'description',
        'working_hours',
        'is_active'
    )
    fields = (
        'location',
        'price_description',
        'description',
        'photo_url',
        'tag_list',
        'working_hours',
        'is_active'
    )
    search_fields = ('location__location_name',)
    list_display_links = ('location',)
    empty_value_display = _('Not defined')
    filter_horizontal = ('tag_list',)

    def loc_court_name(self, obj):
        return str(obj.location.location_name)
    loc_court_name.short_description = _('Location name')

    def link_to_location(self, obj):
        link = reverse(
            'admin:courts_courtlocation_change', args=[obj.location.id])
        return format_html(
            f'<a href="{link}">Edit {obj.location.location_name}</a>')
    link_to_location.short_description = 'Edit location'
