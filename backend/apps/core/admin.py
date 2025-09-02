from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .enums import CoreFieldLength
from .models import (
    Contact,
    CurrencyType,
    GameLevel,
    InfoPage,
    InfoSection,
    Tag
)


class BaseNameAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)
    ordering = ('name',)
    empty_value_display = _('Not defined')
    list_per_page = CoreFieldLength.ADMIN_LIST_PER_PAGE.value


class BaseChoicesAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    list_display = ('id', 'name', 'get_display_name')
    list_filter = ('name',)
    ordering = ('name',)
    empty_value_display = _('Not defined')
    list_per_page = CoreFieldLength.ADMIN_LIST_PER_PAGE.value

    @admin.display(description=_('Title'))
    def get_display_name(self, obj):
        return obj.get_name_display()


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('id', 'contact_type', 'contact')
    search_fields = ('contact', 'contact_type')
    ordering = ('contact',)
    empty_value_display = _('Not defined')
    list_per_page = CoreFieldLength.ADMIN_LIST_PER_PAGE.value


@admin.register(Tag)
class TagAdmin(BaseNameAdmin):
    pass


@admin.register(GameLevel)
class GameLevelAdmin(BaseChoicesAdmin):
    pass


@admin.register(InfoSection)
class InfoSectionAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'page', 'order', 'short_content')
    list_display_links = ('title',)
    list_filter = ('page',)
    search_fields = ('title', 'content')
    ordering = ('page', 'order')
    empty_value_display = _('Not defined')
    list_per_page = CoreFieldLength.ADMIN_LIST_PER_PAGE.value

    @admin.display(description=_('Contents (in short)'))
    def short_content(self, obj):
        return (
            (
                obj.content[:CoreFieldLength.ADMIN_INFO_SHORT_CONTENT.value]
                + '...'
            )
            if obj.content
                and (
                    len(obj.content)
                    > CoreFieldLength.ADMIN_INFO_SHORT_CONTENT.value
                )
            else obj.content
        )


@admin.register(InfoPage)
class InfoPageAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'tag')
    list_display_links = ('title',)
    list_filter = ('tag',)
    search_fields = ('title',)
    ordering = ('title',)
    empty_value_display = _('Not defined')
    list_per_page = CoreFieldLength.ADMIN_LIST_PER_PAGE.value


@admin.register(CurrencyType)
class CurrencyTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'currency_type', 'currency_name')
    search_fields = ('currency_type', 'currency_name')
    ordering = ('currency_type',)
    empty_value_display = _('Not defined')
    list_per_page = CoreFieldLength.ADMIN_LIST_PER_PAGE.value
