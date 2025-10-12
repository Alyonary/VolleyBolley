import pytest
from django.contrib.auth import get_user_model

from apps.locations.models import City, Country
from apps.players.constants import BASE_PAYMENT_DATA
from apps.players.models import Payment, Player

User = get_user_model()


@pytest.fixture
def user_data():
    return {
        'first_name': 'TestName',
        'last_name': 'TestLastName',
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'TestPass123',
        'phone_number': '+12345678900',
    }


@pytest.fixture
def bulk_users_data():
    return [
        {
            'first_name': 'TestName1',
            'last_name': 'TestLastName1',
            'username': 'testuser1',
            'email': 'test1@example.com',
            'password': 'TestPass1',
            'phone_number': '+12345678901',
        },
        {
            'first_name': 'TestName2',
            'last_name': 'TestLastName2',
            'username': 'testuser2',
            'email': 'test2@example.com',
            'password': 'TestPass2',
            'phone_number': '+12345678902',
        },
        {
            'first_name': 'TestName3',
            'last_name': 'TestLastName3',
            'username': 'testuser3',
            'email': 'test3@example.com',
            'password': 'TestPass3',
            'phone_number': '+12345678903',
        },
        {
            'first_name': 'TestName4',
            'last_name': 'TestLastName4',
            'username': 'testuser4',
            'email': 'test4@example.com',
            'password': 'TestPass4',
            'phone_number': '+12345678904',
        },
    ]


@pytest.fixture
def create_user(user_data):
    return User.objects.create_user(**user_data)


@pytest.fixture
def active_user(user_data):
    user = User.objects.create_user(**user_data)
    user.is_active = True
    user.save()
    return user


@pytest.fixture
def user_generated_after_login(active_user):
    player, _ = Player.objects.get_or_create(user=active_user)
    player.is_registered = False
    payments = []
    if len(Payment.objects.filter(player=player)) == 0:
        for data in BASE_PAYMENT_DATA:
            # Create a Payment instance for each dictionary
            payment = Payment(
                player=player,
                payment_type=data['payment_type'],
                payment_account=data['payment_account'],
                is_preferred=data['is_preferred']
            )
            payments.append(payment)
        Payment.objects.bulk_create(payments)
    player.save()
    return player.user


@pytest.fixture
def user_with_registered_player(
    user_generated_after_login,
    player_data_for_registration
):
    player, _ = Player.objects.get_or_create(user=user_generated_after_login)
    player.country = Country.objects.filter(
        id=player_data_for_registration.get('country')
    ).first()
    player.city = City.objects.filter(
        id=player_data_for_registration.get('city')
    ).first()

    rating = player.rating
    rating.grade = player_data_for_registration.get('level')
    rating.save()

    user = player.user
    user.first_name = player_data_for_registration.get('first_name')
    user.last_name = player_data_for_registration.get('last_name')
    user.save()

    player.gender = player_data_for_registration.get('gender')
    player.date_of_birth = player_data_for_registration.get('date_of_birth')
    player.is_registered = True
    player.save()

    return player.user


@pytest.fixture
def bulk_create_users(bulk_users_data):
    return [User.objects.create(**user) for user in bulk_users_data]
