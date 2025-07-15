from django.contrib import admin

from .models import Court, Location


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'longitude',
        'latitude',
        'court_name',
        'name')
    search_fields = ('court_name',)
    list_filter = ('name',)
    empty_value_display = 'Не задано'
    list_display_links = ('id', 'name')


@admin.register(Court)
class CourtAdmin(admin.ModelAdmin):
    list_display = (
        'location',
        'price_description',
        'description',
        'photo_url',
        'working_hours',
        'is_active'
    )
    fields = (
        'location',
        'price_description',
        'description',
        'contacts_list',
        'photo_url',
        'tag_list',
        'working_hours',
        'is_active'
    )
    search_fields = ('name',)
    list_display_links = ('location',)
    empty_value_display = 'Не задано'
    filter_horizontal = ('tag_list', 'contacts_list')
