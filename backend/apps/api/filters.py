import django_filters
from django.db.models import Q, Case, When, IntegerField

from apps.players.models import Player


class PlayersFilter(django_filters.FilterSet):
    """Filter for Player model.
    Allows filtering by first name, last name.
    """

    search = django_filters.CharFilter(method="search_filter")

    def search_filter(self, queryset, name, value):
        """Filter by first_name OR last_name containing the search value.
        For Thailand users - also filters by location proximity.
        For Cyprus users - location is ignored.
        Results are sorted by relevance (exact match > starts with > contains).
        """
        if not value:
            return queryset

        relevance_sort = Case(
            When(user__first_name__iexact=value, then=1),
            When(user__last_name__iexact=value, then=1),
            When(user__first_name__istartswith=value, then=2),
            When(user__last_name__istartswith=value, then=2),
            default=3,
            output_field=IntegerField(),
        )

        request = getattr(self, "request", None)
        current_user_player = Player.objects.get(user=request.user)
        current_location = current_user_player.location
        queryset = queryset.exclude(user=request.user)
        if current_location.country == "Thailand":
            filtered_queryset = (
                queryset.filter(
                    (
                        Q(user__first_name__icontains=value)
                        | Q(user__last_name__icontains=value)
                    )
                    & Q(location__city=current_location.city)
                )
                .annotate(relevance=relevance_sort)
                .order_by("relevance", "user__first_name")
            )
        else:
            filtered_queryset = (
                queryset.filter(
                    (
                        Q(user__first_name__icontains=value)
                        | Q(user__last_name__icontains=value)
                    )
                    & Q(location__country=current_location.country)
                )
                .annotate(relevance=relevance_sort)
                .order_by("relevance", "user__first_name")
            )

        return filtered_queryset

    class Meta:
        model = Player
        fields = [
            "search",
        ]
