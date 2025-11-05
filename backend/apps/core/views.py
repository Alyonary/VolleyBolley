from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.models import FAQ
from apps.core.permissions import IsRegisteredPlayer


class FAQView(APIView):
    """
    View to retrieve the active FAQ.
    """
    permission_classes = [IsRegisteredPlayer]

    @swagger_auto_schema(
        tags=['faq'],
        operation_summary="Get FAQ text",
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
                            description='FAQ text in markdown format'
                            )
                    }
                )
                ),
            404: openapi.Response(
                'Not found',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'faq': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            default='No active FAQ available.'
                            )
                    }
                )
            ),
        },
        security=[{'Bearer': []}, {'JWT': []}],
    )
    def get(self, request, *args, **kwargs):
        faq = FAQ.get_active()
        if faq:
            return Response({"faq": faq.content})
        return Response({"faq": "No active FAQ available."}, status=404)
