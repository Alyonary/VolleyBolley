import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

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
