from django.db.models import Prefetch, Q, QuerySet
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
        if not value:
            return queryset
        now = timezone.now()
        has_future_games = Game.objects.filter(
            court_id=OuterRef('pk'),
            start_time__gte=now
        )
        has_future_tournaments = Tournament.objects.filter(
            court_id=OuterRef('pk'),
            start_time__gte=now
        )
        queryset = queryset.filter(
            Exists(has_future_games) | Exists(has_future_tournaments)
        )

        events_detail = self.data.get('events_detail', '')
        if str(events_detail).lower() in ('true', '1'):
            queryset = queryset.prefetch_related(
                Prefetch(
                    'games', 
                    queryset=Game.objects.filter(start_time__gte=now).order_by('start_time')
                ),
                Prefetch(
                    'tournaments', 
                    queryset=Tournament.objects.filter(start_time__gte=now).order_by('start_time')
                )
            )
        return queryset
