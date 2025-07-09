from rest_framework.generics import ListCreateAPIView

from .models import Court
from .serializers import CourtSerializer


class CourtsView(ListCreateAPIView):

    queryset = Court.objects.all()
    serializer_class = CourtSerializer
