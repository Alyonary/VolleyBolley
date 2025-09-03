from django.contrib import admin

from apps.notifications.models import Device


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'player',
        'masked_token',
        'platform',
        'is_active',
        'created_at',
        'updated_at'
    ]
    search_fields = ['player__user__username', 'platform']
    list_filter = ['platform', 'is_active', 'created_at', 'updated_at']
    ordering = ['-created_at']
    # readonly_fields = [
    #     'created_at',
    #     'updated_at',
    #     'masked_token',
    #     'player',
    #     'platform',
    #     'token'
    # ]
    empty_value_display = '-empty-'
    list_display_links = ['id']
    
    def masked_token(self, obj):
        """Show only first and last 4 characters of the token."""
        if obj.token and len(obj.token) > 8:
            return f'{obj.token[:4]}...{obj.token[-4:]}'
        return '****'
    
    masked_token.short_description = 'Token'
    
    # def has_add_permission(self, request):
    #     """Disable adding new devices through admin."""
    #     return False
    
    def has_change_permission(self, request, obj=None):
        """Disable editing devices through admin."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Allow only deletion of devices."""
        return True
    
    fields = [
        'player',
        'platform',
        'is_active',
        'token'
    ]
