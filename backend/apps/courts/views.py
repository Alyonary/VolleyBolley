from django_filters import rest_framework as filters
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet

from apps.core.permissions import IsRegisteredPlayer
from apps.courts.filters import CourtFilter
from apps.courts.models import Court
from apps.courts.serializers import CourtSerializer


class CourtViewSet(mixins.ListModelMixin, GenericViewSet):
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

    def get_queryset(self):
        player = getattr(self.request.user, 'player', None)
        country = getattr(player, 'country', None)
        city = getattr(player, 'city', None)
        if country is None or city is None:
            return super().get_queryset()

        if country.name == 'Cyprus':
            return super().get_queryset().filter(location__country=country)

        if country.name == 'Thailand':
            return super().get_queryset().filter(location__city=city)
        return super().get_queryset()

    @swagger_auto_schema(
        tags=['courts'],
        operation_summary='List of filtered courts',
        operation_description="""
        **Returns:** a list of courts filtered depending on players location.
        """,
        responses={
            200: openapi.Response('Success', CourtSerializer(many=True)),
            401: 'Unauthorized',
            403: 'Forbidden',
        },
        security=[{'Bearer': []}, {'JWT': []}],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
