from rest_framework.viewsets import ModelViewSet

from .models import Court
from .serializers import CourtSerializer


class CourtViewSet(ModelViewSet):

    queryset = Court.objects.all()
    serializer_class = CourtSerializer
