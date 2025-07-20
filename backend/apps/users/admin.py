from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.users.models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'username',
        'first_name',
        'last_name',
        'email',
        'phone_number',
        'is_admin',
        'is_staff',
        'is_active',
        'date_joined',
        'last_login',
    )
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('is_admin', 'is_staff', 'is_active')
    empty_value_display = _('Not defined')
    list_display_links = ('id', 'username')
