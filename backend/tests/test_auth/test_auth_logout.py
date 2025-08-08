import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


@pytest.mark.django_db
def test_user_logout(api_client, active_user):
    refresh = RefreshToken.for_user(active_user)
    # Send request to logout
    response = api_client.post(
        reverse('api:logout'),
        {'refresh': str(refresh)},
        format='json'
    )
    assert response.status_code == status.HTTP_205_RESET_CONTENT
    # Check if token is in blacklist
    assert BlacklistedToken.objects.filter(
        token__jti=refresh['jti']
    ).exists()
