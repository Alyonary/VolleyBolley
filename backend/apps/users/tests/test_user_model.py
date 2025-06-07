import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from rest_framework.test import APIClient

from apps.users.models import Location

User = get_user_model()


@pytest.mark.django_db
class TestUserModel:
    def test_create_user_with_defaults(self):
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123',
            phone_number='+12345678901',
        )

        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.phone_number.as_e164 == '+12345678901'
        assert user.game_skill_level == User.GameSkillLevel.BEGINNER
        assert user.rating == 1000
        assert not user.avatar
        assert user.location is None

    def test_phone_number_uniqueness(self):
        User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='123',
            phone_number='+11111111111',
        )

        with pytest.raises(IntegrityError):
            User.objects.create_user(
                username='user2',
                email='user2@example.com',
                password='123',
                phone_number='+11111111111',
            )

    def test_game_skill_level_choices(self):
        user = User.objects.create_user(
            username='gamer',
            email='gamer@example.com',
            password='abc',
            phone_number='+19876543210',
            game_skill_level=User.GameSkillLevel.PRO,
        )
        assert user.game_skill_level == 'pro'

    def test_user_location_relation(self):
        location = Location.objects.create(country='Cyprus', city='Nicosia')
        user = User.objects.create_user(
            username='locuser',
            email='loc@example.com',
            password='123',
            phone_number='+19999999999',
            location=location,
        )
        assert user.location.country == 'Cyprus'
        assert user.location.city == 'Nicosia'

    def test_obtain_jwt_token(self):
        client = APIClient()
        User.objects.create_user(
            username='testuser_token',
            email='token@example.com',
            password='password123',
            phone_number='+12236532323'
        )
        response = client.post('/api/auth/token/', {
            'username': 'testuser_token',
            'password': 'password123',
        }, format='json')

        assert response.status_code == 200
        assert 'access' in response.data
        assert 'refresh' in response.data

    def test_refresh_jwt_token(self):
        client = APIClient()
        User.objects.create_user(
            username='testuser_token',
            email='token@example.com',
            password='password123',
            phone_number='+12236532323'
        )
        response = client.post('/api/auth/token/', {
            'username': 'testuser_token',
            'password': 'password123',
        }, format='json')

        assert response.status_code == 200

        refresh_token = response.data['refresh']

        refresh_response = client.post('/api/auth/token/refresh/', {
        'refresh': refresh_token,
        }, format='json')

        assert refresh_response.status_code == 200
        assert 'access' in refresh_response.data
        assert isinstance(refresh_response.data['access'], str)
        assert refresh_response.data['access']
