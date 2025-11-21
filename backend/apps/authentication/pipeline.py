from apps.authentication.exceptions import OAuthSuccessException
from apps.authentication.utils import get_serialized_data


def generate_json_response(
    strategy, details, backend, user=None, *args, **kwargs
):
    """Lounge a pipeline to generate json response to client."""
    if not user:
        return

    serializer = get_serialized_data(user)
    strategy.request.oauth_response_data = serializer.data
    strategy.session_set('oauth_response_data', serializer.data)

    return


def raise_oauth_success(
    strategy, details, backend, user=None, *args, **kwargs
):
    """Raise exception to break redirect after successful social auth."""
    if (
        user
        and (
            strategy.session_get('oauth_response_data')
            or strategy.request.oauth_response_data
        )
        and (
            not strategy.session_get('via_access_token')
            or not hasattr(strategy.request, 'via_access_token')
        )
    ):
        raise OAuthSuccessException()
    return
