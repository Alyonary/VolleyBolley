"""The module that defines access rights in the application."""

from rest_framework.permissions import SAFE_METHODS, IsAuthenticatedOrReadOnly


class IsHostOrReadOnly(IsAuthenticatedOrReadOnly):
    """Verification of access rights to the authorship of the object."""

    def has_object_permission(self, request, view, obj):
        return (request.method in SAFE_METHODS
                or request.user == obj.host)
