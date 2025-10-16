from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.event.enums import EventIntEnums
from apps.event.models import Game, GameInvitation, Tourney, TourneyTeam


class BaseEventAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'court',
        'host',
        'is_active',
        'is_private',
        'gender'
    )
    list_display_links = ('id',)
    search_fields = ('message',)
    list_filter = ('court', 'is_active', 'is_private')
    filter_horizontal = ('player_levels', 'players')
    empty_value_display = _('Not defined',)
    autocomplete_fields = ('court', 'host',)
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('id',)
    list_per_page = EventIntEnums.ADMIN_LIST_PER_PAGE.value


@admin.register(Game)
class GameAdmin(BaseEventAdmin):
    pass


class TeamInline(admin.TabularInline):
    model = TourneyTeam
    extra = 1


@admin.register(Tourney)
class TourneyAdmin(BaseEventAdmin):
    list_display = BaseEventAdmin.list_display + (
        'is_individual',
        'maximum_teams',
    )
    list_filter = BaseEventAdmin.list_filter + (
        'is_individual',
    )
    filter_horizontal = ('player_levels',)
    inlines = [TeamInline]


@admin.register(GameInvitation)
class GameInvitationAdmin(admin.ModelAdmin):
    list_display = ('id', 'content_object', 'host', 'invited')
    search_fields = ('content_object', 'host', 'invited')
    empty_value_display = _('Not defined')
    list_per_page = EventIntEnums.ADMIN_LIST_PER_PAGE.value
