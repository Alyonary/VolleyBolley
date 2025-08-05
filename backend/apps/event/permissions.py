'''Модуль, определяющий права доступа в приложении.'''

from rest_framework.permissions import SAFE_METHODS, IsAuthenticatedOrReadOnly


class IsHostOrReadOnly(IsAuthenticatedOrReadOnly):
    '''Проверка прав доступа на авторство объекта.'''

    def has_object_permission(self, request, view, obj):
        return (request.method in SAFE_METHODS
                or request.user == obj.host)
