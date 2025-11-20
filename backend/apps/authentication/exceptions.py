from rest_framework import status
from rest_framework.exceptions import APIException


class OAuthSuccessException(APIException):
    """
    Breakpoint for social-auth pipeline.

    Raises exception to prevent redirect after successful social auth pipeline.
    """

    status_code = status.HTTP_200_OK
    default_detail = 'OAuth authentication successful'
    default_code = 'oauth_success'
