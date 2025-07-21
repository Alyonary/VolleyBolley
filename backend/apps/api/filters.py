import django_filters

from apps.players.models import Player


class PlayersFilter(django_filters.FilterSet):
    """Filter for Player model.
    Allows filtering by username, first name, last name, location,
    and level type.
    """

    username = django_filters.CharFilter(
        field_name="user__username", lookup_expr="icontains"
    )
    first_name = django_filters.CharFilter(
        field_name="user__first_name", lookup_expr="icontains"
    )
    last_name = django_filters.CharFilter(
        field_name="user__last_name", lookup_expr="icontains"
    )
    location = django_filters.CharFilter(
        field_name="location__city", lookup_expr="icontains"
    )
    level_type = django_filters.CharFilter(
        field_name="level", lookup_expr="exact"
    )

    class Meta:
        model = Player
        fields = [
            "username",
            "first_name",
            "last_name",
            "location",
            "level_type",
        ]
