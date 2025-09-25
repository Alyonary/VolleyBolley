from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.notifications.models import Device, NotificationsBase


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    """
    Admin interface for managing user devices for push notifications.
    Provides read-only access to device details and allows deletion only.
    """

    list_display = [
        'id',
        'player',
        'masked_token',
        'platform',
        'is_active',
        'created_at',
        'updated_at',
    ]
    search_fields = ['player__user__username', 'platform']
    list_filter = ['platform', 'is_active', 'created_at', 'updated_at']
    ordering = ['-created_at']
    readonly_fields = [
        'created_at',
        'updated_at',
        'masked_token',
        'player',
        'platform',
        'token',
    ]
    empty_value_display = '-empty-'
    list_display_links = ['id']

    def masked_token(self, obj):
        """Show only first and last 4 characters of the token."""

        if obj.token and len(obj.token) > 8:
            return f'{obj.token[:4]}...{obj.token[-4:]}'
        return '****'

    masked_token.short_description = 'Token'

    def has_add_permission(self, request):
        """Disable adding new devices through admin."""
        return False

    def has_change_permission(self, request, obj=None):
        """Disable editing devices through admin."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Allow only deletion of devices."""
        return True

    fields = [
        'player',
        'platform',
        'masked_token',
        'is_active',
        'created_at',
        'updated_at',
    ]


@admin.register(NotificationsBase)
class NotificationsBaseAdmin(admin.ModelAdmin):
    """
    Admin interface for managing notification templates.
    Allows full CRUD operations on notification templates.
    """

    list_display = ['id', 'type', 'title', 'screen']
    search_fields = ['type', 'title', 'screen']
    ordering = ['type']
    readonly_fields = ['id']
    empty_value_display = _('-empty-')
    list_display_links = ['id', 'type']
    fields = ['type', 'title', 'body', 'screen', 'id']