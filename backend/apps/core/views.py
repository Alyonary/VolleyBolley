from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.models import FAQ, CurrencyType
from apps.core.permissions import IsRegisteredPlayer
from apps.core.serializers import CurrencyListSerializer
from apps.core.swagger_schemas import CURRENCIES_GET_SCHEMA, FAQ_GET_SCHEMA


class FAQView(APIView):
    """
    View to retrieve the active FAQ.
    """

    permission_classes = [IsRegisteredPlayer]

    @swagger_auto_schema(**FAQ_GET_SCHEMA)
    def get(self, request, *args, **kwargs):
        faq = FAQ.get_active()
        if faq:
            return Response({'faq': faq.content})
        return Response(
            {'faq': 'No active FAQ available.'},
            status=status.HTTP_404_NOT_FOUND,
        )


class CurrenciesView(APIView):
    """
    View to retrieve all available currency types.
    """

    permission_classes = [AllowAny]

    @swagger_auto_schema(**CURRENCIES_GET_SCHEMA)
    def get(self, request, *args, **kwargs):
        """Retrieve all currency types."""

        serializer = CurrencyListSerializer(
            {'currencies': CurrencyType.objects.all()}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)
