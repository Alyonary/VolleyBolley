import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.event.models import Game
from apps.locations.models import City, Country
from apps.players.models import Player

User = get_user_model()


@pytest.fixture
def game_data(
    bulk_create_users,
    currency_type,
    court_obj_with_tag,
    payment_account_revolut,
    gender_men,
    game_levels
):
    return {
        'court_id': court_obj_with_tag.id,
        'message': 'Test game in Thailand',
        'start_time': '2025-08-21 15:30',
        'end_time': '2025-08-21 18:30',
        'gender': gender_men,
        'player_levels': [
            game_levels
        ],
        'is_private': False,
        'max_players': 5,
        'price_per_person': '5',
        'payment_type': payment_account_revolut,
        'players': bulk_create_users,
        'host': payment_account_revolut.owner,
        'currency_type': currency_type,
        'payment_account': payment_account_revolut.payment_account
    }


@pytest.fixture
def game_without_players(game_data):
    game_data.pop('players')
    levels = game_data.pop('player_levels')
    game = Game.objects.create(**game_data)
    game.player_levels.set(levels)
    return game


@pytest.fixture
def game_with_players(game_data):
    players = game_data.pop('players')
    levels = game_data.pop('player_levels')
    game = Game.objects.create(**game_data)
    game.players.set(players)
    game.player_levels.set(levels)
    return game


@pytest.fixture
def game_for_args(game_with_players):
    return (game_with_players.id,)


@pytest.fixture
def client():
    client = APIClient()
    return client


@pytest.fixture
def authored_api_client(active_user, client):
    client.force_authenticate(active_user)
    return client


@pytest.fixture
def another_user(user_data):
    user_data['username'] = 'AnotherUser'
    user_data['phone_number'] = '88005555535'
    return User.objects.create_user(**user_data)


@pytest.fixture
def user_player(active_user):
    country, _ = Country.objects.get_or_create(name='Thailand')
    city, _ = City.objects.get_or_create(country=country, name='Pattaya')
    return Player.objects.create(
        user=active_user,
        gender='MALE',
        level='LIGHT',
        country=country,
        city=city
    )


@pytest.fixture
def another_user_player(another_user):
    country, _ = Country.objects.get_or_create(name='Cyprus')
    city, _ = City.objects.get_or_create(country=country, name='Limassol')
    return Player.objects.create(
        user=another_user,
        gender='MALE',
        level='LIGHT',
        country=country,
        city=city
    )


@pytest.fixture
def another_user_client(another_user, client):
    client.force_authenticate(another_user)
    return client


@pytest.fixture
def another_game_cyprus(another_user, game_data, another_court_obj):
    game_data['court_id'] = another_court_obj.id
    game_data['message'] = 'Test game in Cyprus'
    game_data['host'] = another_user
    game = Game.objects.create(**game_data)
    return game
