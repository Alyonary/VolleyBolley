from django.contrib import admin

from apps.users.models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    search_fields = ('username', 'email', 'first_name', 'last_name')
# todo пришлось мини сделать, чтобы запустилась админка и миграции прошли
