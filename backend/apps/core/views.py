from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.models import FAQ
from apps.core.permissions import IsRegisteredPlayer


class FAQView(APIView):
    """
    View to retrieve the active FAQ.
    """
    permission_classes = [IsRegisteredPlayer]

    def get(self, request, *args, **kwargs):
        faq = FAQ.get_active()
        if faq:
            return Response({"faq": faq.content})
        return Response({"faq": "No active FAQ available."}, status=404)