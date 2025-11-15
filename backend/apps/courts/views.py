from django_filters import rest_framework as filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from apps.courts.filters import CourtFilter
from apps.courts.models import Court
from apps.courts.serializers import CourtSerializer


class CourtViewSet(ModelViewSet):
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
    permission_classes = (IsAuthenticated,)

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
