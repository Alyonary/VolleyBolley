import logging

from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.locations.models import Country
from apps.locations.serializers import CountryListSerializer
from apps.locations.swagger_schemas import LOCATIONS_COUNTRIES_GET_SCHEMA

logger = logging.getLogger(__name__)


class CountryListView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(**LOCATIONS_COUNTRIES_GET_SCHEMA)
    def get(self, request):
        try:
            countries = Country.objects.prefetch_related('cities').all()
            serializer = CountryListSerializer({'countries': countries})

            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            error_msg = f'Internal server error: {e}.'
            logger.error(error_msg)

            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
