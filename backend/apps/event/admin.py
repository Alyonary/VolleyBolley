from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.event.enums import EventFieldLength
from apps.event.models import Game, Tourney, GameInvitation


class BaseEventAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'court',
        'host',
        'is_active',
        'is_private',
    )
    list_display_links = ('id',)
    search_fields = ('message',)
    list_filter = ('court', 'is_active', 'is_private')
    filter_horizontal = ('player_levels', 'players')
    empty_value_display = _('Not defined',)
    autocomplete_fields = ('court', 'host', 'gender')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('id',)
    list_per_page = EventFieldLength.ADMIN_LIST_PER_PAGE.value


@admin.register(Game)
class GameAdmin(BaseEventAdmin):
    pass


@admin.register(Tourney)
class TourneyAdmin(BaseEventAdmin):
    list_display = BaseEventAdmin.list_display + (
        'is_individual',
        'maximum_teams',
    )
    list_filter = BaseEventAdmin.list_filter + (
        'is_individual',
    )


@admin.register(GameInvitation)
class GameInvitationAdmin(admin.ModelAdmin):
    list_display = ('id', 'game', 'host', 'invited')
    search_fields = ('game', 'host', 'invited')
    ordering = ('game',)
    empty_value_display = _('Not defined')
    list_per_page = EventFieldLength.ADMIN_LIST_PER_PAGE.value
