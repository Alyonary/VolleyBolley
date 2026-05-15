from django.db.models import Q, QuerySet
from django_filters import rest_framework as filters

from apps.courts.models import Court


class CourtFilter(filters.FilterSet):
    """
    Filter for Court model:
    - search: case-insensitive search by court name
    - active_events: filter courts with active games or tournaments
    """

    search = filters.CharFilter(
        field_name='location__court_name', lookup_expr='icontains'
    )
    active_events = filters.BooleanFilter(method='filter_active_events')

    class Meta:
        model = Court
        fields = (
            'search',
            'active_events',
        )

    def filter_active_events(
        self, queryset: QuerySet, name: str, value: bool
    ) -> QuerySet:
        """Filter courts that have at least one associated event."""
        if value:
            return queryset.filter(
                Q(games__isnull=False) | Q(tourneys__isnull=False)
            ).distinct()
        return queryset
