import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from apps.users.models import Location

User = get_user_model()


@pytest.mark.django_db
class TestUserModel:
    def test_create_user_with_defaults(self):
        location = Location.objects.create(country='Cyprus', city='Nicosia')
        user = User.objects.create_user(
            first_name='NameTestUser',
            last_name='LastnameTestUser',
            gender='M',
            birth_date='1991-01-01',
            email='testemail@example.com',
            password='password123',
            phone_number='+12345678901',
            location=location,
        )

        assert user.first_name == 'NameTestUser'
        assert user.last_name == 'LastnameTestUser'
        assert user.gender == 'M'
        assert user.birth_date == '1991-01-01'
        assert user.email == 'testemail@example.com'
        assert user.phone_number.as_e164 == '+12345678901'
        assert user.location == location

    def test_phone_number_uniqueness(self):
        User.objects.create_user(
            first_name='NameTestUser',
            last_name='LastnameTestUser',
            email='user1@example.com',
            password='123',
            phone_number='+11111111111',
        )

        with pytest.raises(IntegrityError):
            User.objects.create_user(
                first_name='NameTestUserSecond',
                last_name='LastnameTestUserSecond',
                email='user2@example.com',
                password='123',
                phone_number='+11111111111',
            )

    def test_email_uniqueness(self):
        User.objects.create_user(
            first_name='NameTestUser',
            last_name='LastnameTestUser',
            email='uniqueemail@example.com',
            password='123',
            phone_number='+11111111111',
        )

        with pytest.raises(IntegrityError):
            User.objects.create_user(
                first_name='NameTestUserSecond',
                last_name='LastnameTestUserSecond',
                email='uniqueemail@example.com',
                password='123',
                phone_number='+222222222',
            )

    def test_user_location_relation(self):
        location = Location.objects.create(country='Cyprus', city='Nicosia')
        user = User.objects.create_user(
            first_name='NameTestUserSecond',
            last_name='LastnameTestUserSecond',
            email='loc@example.com',
            password='123',
            phone_number='+19999999999',
            location=location,
        )
        assert user.location.country == 'Cyprus'
        assert user.location.city == 'Nicosia'
