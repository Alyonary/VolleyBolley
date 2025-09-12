from django_filters import rest_framework as filters
from rest_framework.viewsets import ModelViewSet

from .filters import CourtFilter
from .models import Court
from .serializers import CourtSerializer


class CourtViewSet(ModelViewSet):
    http_method_names = ['get',]
    queryset = Court.objects.select_related(
        'location').prefetch_related('contacts', 'tag_list').all()

    serializer_class = CourtSerializer
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = CourtFilter
