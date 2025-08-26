# apps/api/middleware.py
from django.http import JsonResponse

from .exceptions import OAuthSuccessException
from .serializers import LoginSerializer


class OAuthResponseMiddleware:
    """Set up custom breakpoint in social-auth pipeline."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        """Break social-auth pipeline and return JsonResponse."""
        if isinstance(exception, OAuthSuccessException):
            response_data = request.session.get('oauth_response_data')
            if response_data:
                serializer = LoginSerializer(response_data)
                return JsonResponse(serializer.data, status=200)

        return None
