from django.db.models import QuerySet
from django_filters import rest_framework as filters
from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins
from rest_framework.request import Request
from rest_framework.viewsets import GenericViewSet

from apps.core.permissions import IsRegisteredPlayer
from apps.courts.filters import CourtFilter
from apps.courts.models import Court
from apps.courts.serializers import CourtSerializer, CourtWithEventsSerializer
from apps.courts.swagger_schemas import COURTS_LIST_SCHEMA, COURTS_RETRIEVE_SCHEMA


class CourtViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, GenericViewSet
):
    """ViewSet for listing and retrieving courts with event details."""

    http_method_names = [
        'get',
    ]
    queryset = (
        Court.objects.select_related('location')
        .prefetch_related('contacts', 'tag_list')
        .all()
    )

    serializer_class = CourtSerializer
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = CourtFilter
    permission_classes = [IsRegisteredPlayer]

    def _has_events_detail(self) -> bool:
        """Check if the events_detail flag is explicitly requested."""
        val = self.request.query_params.get('events_detail', '')
        return val.lower() in ('true', '1')

    def get_serializer_class(self):
        """Return detailed serializer only if requested on retrieve action."""
        if self.action == 'retrieve' and self._has_events_detail():
            return CourtWithEventsSerializer
        return CourtSerializer

    def get_queryset(self):
        """Filter queryset by geography and prefetch events conditionally."""
        queryset: QuerySet = super().get_queryset()
        if self.action == 'retrieve' and self._has_events_detail():
            queryset: QuerySet = queryset.prefetch_related('games', 'tourneys')

        player = getattr(self.request.user, 'player', None)
        country = getattr(player, 'country', None)
        city = getattr(player, 'city', None)

        if country is None or city is None:
            return queryset
        return queryset.filter(location__country=country)

    @swagger_auto_schema(**COURTS_LIST_SCHEMA)
    def list(self, request: Request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(**COURTS_RETRIEVE_SCHEMA)
    def retrieve(self, request: Request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
