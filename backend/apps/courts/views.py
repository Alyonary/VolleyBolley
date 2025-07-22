from django_filters import rest_framework as filters
from rest_framework.viewsets import ModelViewSet

from .filters import CourtFilter
from .models import Court
from .serializers import CourtSerializer


class CourtViewSet(ModelViewSet):

    queryset = Court.objects.prefetch_related('contacts').all()
    serializer_class = CourtSerializer
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = CourtFilter
