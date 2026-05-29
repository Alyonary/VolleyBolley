from django.db.models import QuerySet
from django.http import Http404
from django_filters import rest_framework as filters
from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins
from rest_framework.request import Request
from rest_framework.viewsets import GenericViewSet

from apps.core.permissions import IsRegisteredPlayer
from apps.courts.filters import CourtFilter
from apps.courts.models import Court
from apps.courts.serializers import CourtSerializer, CourtWithEventsSerializer
from apps.courts.swagger_schemas import (
    COURTS_LIST_SCHEMA,
    COURTS_RETRIEVE_SCHEMA,
)


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

    def get_serializer_class(self):
        if self.action == 'retrieve' and self._has_events_detail():
            return CourtWithEventsSerializer
        return CourtSerializer

    def get_queryset(self) -> QuerySet:
        player = getattr(self.request.user, 'player', None)
        country = getattr(player, 'country', None)
        if country is None:
            return Court.objects.none()
        return super().get_queryset().filter(location__country=country)

    @swagger_auto_schema(**COURTS_LIST_SCHEMA)
    def list(self, request: Request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(**COURTS_RETRIEVE_SCHEMA)
    def retrieve(self, request: Request, *args, **kwargs):
        instance = self.get_object()
        player = getattr(request.user, 'player', None)
        player_country = getattr(player, 'country', None)
        court_country = getattr(instance.location, 'country', None)
        if (
            not player_country
            or not court_country
            or player_country != court_country
        ):
            raise Http404('Court not found')
        return super().retrieve(request, *args, **kwargs)
