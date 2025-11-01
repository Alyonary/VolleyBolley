from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Player


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'get_first_name',
        'get_last_name',
        'gender',
        'country',
        'city',
        'rating',
    )
    search_fields = ('user__first_name', 'user__last_name')
    list_filter = (
        'gender',
        'country',
        'city',
    )
    empty_value_display = _('Not defined')
    list_display_links = ('id', 'user')

    def get_first_name(self, obj):
        return obj.user.first_name

    get_first_name.short_description = _('First name')

    def get_last_name(self, obj):
        return obj.user.last_name

    get_last_name.short_description = _('Last name')
