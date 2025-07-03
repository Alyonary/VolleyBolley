import pytest
from django.contrib.auth import get_user_model
from rest_framework import status

User = get_user_model()


@pytest.mark.django_db
class TestUserRegistration:
    def test_user_registration(self, api_client, user_data):
        url = '/api/auth/users/'
        response = api_client.post(url, user_data)
        assert response.status_code == status.HTTP_201_CREATED
        assert User.objects.filter(email=user_data['email']).exists()

    def test_get_current_user_unauthorized(self, api_client):
        url = '/api/auth/users/me/'
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_current_user_authorized(self, api_client, active_user):
        url = '/api/auth/users/me/'
        api_client.force_authenticate(user=active_user)
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == active_user.email

    def test_get_user_list(self, api_client, active_user, bulk_create_users):
        url = '/api/auth/users/'
        api_client.force_authenticate(user=active_user)
        for user in bulk_create_users:
            user.refresh_from_db()
        response = api_client.get(url)
        assert len(response.data) == len(bulk_create_users) + 1

    def test_set_password(self, api_client, active_user):
        url = '/api/auth/users/set_password/'
        data = {
            'new_password': 'newpassword123',
            'current_password': 'TestPass123',
        }
        api_client.force_authenticate(user=active_user)
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        active_user.refresh_from_db()
        assert active_user.check_password(data['new_password'])
