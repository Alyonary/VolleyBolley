from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.models import FAQ, CurrencyType
from apps.core.permissions import IsRegisteredPlayer
from apps.core.serializers import CurrencyListSerializer


class FAQView(APIView):
    """
    View to retrieve the active FAQ.
    """

    permission_classes = [IsRegisteredPlayer]

    @swagger_auto_schema(
        tags=['faq'],
        operation_summary='Get FAQ text',
        operation_description="""
        **Returns:** FAQ text in markdown format.
        """,
        responses={
            200: openapi.Response(
                'Success',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'faq': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='FAQ text in markdown format',
                        )
                    },
                ),
            ),
            404: openapi.Response(
                'Not found',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'faq': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            default='No active FAQ available.',
                        )
                    },
                ),
            ),
        },
        security=[{'Bearer': []}, {'JWT': []}],
    )
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

    @swagger_auto_schema(
        tags=['currencies'],
        operation_summary='Get all currency types',
        operation_description="""
        **Returns:** List of all available currency types.
        """,
        responses={
            200: openapi.Response('Success', CurrencyListSerializer()),
        },
    )
    def get(self, request, *args, **kwargs):
        """Retrieve all currency types."""

        serializer = CurrencyListSerializer(
            {'currencies': CurrencyType.objects.all()}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)
