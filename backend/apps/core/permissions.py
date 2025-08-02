from rest_framework import permissions


class IsPlayer(permissions.IsAuthenticated):

    def has_object_permission(self, request, view, obj):
        return bool(request.user == obj.user)
