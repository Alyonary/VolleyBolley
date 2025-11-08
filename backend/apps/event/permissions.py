"""The module that defines access rights in the application."""

from rest_framework.permissions import SAFE_METHODS

from apps.core.permissions import IsRegisteredPlayer


class IsHostOrReadOnly(IsRegisteredPlayer):
    """Verification of access rights to the authorship of the object."""

    def has_object_permission(self, request, view, obj):
        return (request.method in SAFE_METHODS
                or request.user.player == obj.host)

class IsPlayerInEvent(IsRegisteredPlayer):
    """Verification of access rights for players participating in the event."""

    def has_object_permission(self, request, view, obj):
        return (request.method in SAFE_METHODS
                or request.user.player in obj.players.all())
