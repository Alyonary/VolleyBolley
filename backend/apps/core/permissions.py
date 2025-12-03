from rest_framework.permissions import IsAuthenticated


class IsNotRegisteredPlayer(IsAuthenticated):

    def has_permission(self, request, view):
        return bool(
            request.user.is_authenticated
            and request.user
            and not request.user.player.is_registered
        )

    # def has_object_permission(self, request, view, obj):
    #     return bool(
    #         request.user == obj.user
    #         or request.method in SAFE_METHODS
    #     )


class IsRegisteredPlayer(IsNotRegisteredPlayer):

    def has_permission(self, request, view):
        return bool(
            request.user.is_authenticated
            and request.user
            and request.user.player.is_registered
        )
