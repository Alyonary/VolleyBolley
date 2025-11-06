"""The module that defines access rights in the application."""

from rest_framework.permissions import SAFE_METHODS

from apps.core.permissions import IsRegisteredPlayer
from apps.event.models import Game, Tourney


class IsHostOrReadOnly(IsRegisteredPlayer):
    """Verification of access rights to the authorship of the object."""

    def has_object_permission(self, request, view, obj):
        return (request.method in SAFE_METHODS
                or request.user.player == obj.host)


class IsPlayerOrReadOnly(IsRegisteredPlayer):
    """Verification of access rights to the membership of the object."""

    def has_object_permission(self, request, view, obj):

        if request.method in SAFE_METHODS:
            return True
        elif isinstance(obj, Game):
            return request.user.player in obj.players.all()
        elif isinstance(obj, Tourney):
            return request.user.player.id in obj.teams.all().values_list(
                'players', flat=True)
        else:
            False
