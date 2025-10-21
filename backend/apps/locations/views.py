from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.locations.models import Country
from apps.locations.serializers import CountrySerializer


class CountryListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        countries = Country.objects.prefetch_related('cities').all()
        serializer = CountrySerializer(countries, many=True)
        return Response({'countries': serializer.data})
