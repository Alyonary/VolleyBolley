import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.event.models import Game
from apps.locations.models import City, Country
from apps.players.models import Payment, Player

User = get_user_model()


@pytest.fixture
def country_thailand():
    return Country.objects.create(name='Thailand')


@pytest.fixture
def city_in_thailand(country_thailand):
    return City.objects.create(name='Pattaya', country=country_thailand)


@pytest.fixture
def country_cyprus():
    return Country.objects.create(name='Cyprus')


@pytest.fixture
def city_in_cyprus(country_cyprus):
    return City.objects.create(name='Limassol', country=country_cyprus)


@pytest.fixture
def game_data(
    bulk_create_registered_players,
    currency_type_thailand,
    court_thailand,
    payment_account_revolut,
    game_levels_light,
    game_levels_medium,
    player_thailand
):
    return {
        'court_id': court_thailand.id,
        'message': 'Test game in Thailand',
        'start_time': '2025-09-21T15:30:00Z',
        'end_time': '2025-09-21T18:30:00Z',
        'gender': 'MEN',
        'player_levels': [
            game_levels_light,
            game_levels_medium
        ],
        'is_private': False,
        'max_players': 5,
        'price_per_person': '5.00',
        'payment_type': payment_account_revolut.payment_type,
        'players': bulk_create_registered_players,
        'host': player_thailand,
        'currency_type': currency_type_thailand,
        'payment_account': payment_account_revolut.payment_account
    }


@pytest.fixture
def game_thailand(game_data):
    working_data = game_data.copy()
    working_data.pop('players')
    levels = working_data.pop('player_levels')
    game = Game.objects.create(**working_data)
    game.player_levels.set(levels)
    return game


@pytest.fixture
def game_thailand_with_players(game_data):
    working_data = game_data.copy()
    players = working_data.pop('players')
    levels = working_data.pop('player_levels')
    game = Game.objects.create(**working_data)
    game.players.set(players)
    game.player_levels.set(levels)
    return game


@pytest.fixture
def game_for_args(game_thailand):
    return (game_thailand.id,)


@pytest.fixture
def client():
    client = APIClient()
    return client


@pytest.fixture
def api_client_thailand(active_user, client):
    client.force_authenticate(active_user)
    return client


@pytest.fixture
def another_user(user_data):
    user_data['username'] = 'AnotherUser'
    user_data['phone_number'] = '88005555535'
    return User.objects.create_user(**user_data)


@pytest.fixture
def player_thailand(active_user, country_thailand, city_in_thailand):
    return Player.objects.create(
        user=active_user,
        gender='MALE',
        level='LIGHT',
        country=country_thailand,
        city=city_in_thailand
    )


@pytest.fixture
def payment_account_revolut(player_thailand):
    return Payment.objects.create(
        player=player_thailand,
        payment_type='REVOLUT',
        payment_account='test acc'
    )


@pytest.fixture
def player_cyprus(another_user, country_cyprus, city_in_cyprus):
    return Player.objects.create(
        user=another_user,
        gender='MALE',
        level='LIGHT',
        country=country_cyprus,
        city=city_in_cyprus
    )


@pytest.fixture
def api_client_cyprus(another_user, client):
    client.force_authenticate(another_user)
    return client


@pytest.fixture
def game_cyprus(player_cyprus, game_data, court_cyprus):
    working_data = game_data.copy()
    working_data['court_id'] = court_cyprus.id
    working_data['message'] = 'Test game in Cyprus'
    working_data['host'] = player_cyprus
    players = working_data.pop('players')
    levels = working_data.pop('player_levels')
    game = Game.objects.create(**working_data)
    game.players.set(players)
    game.player_levels.set(levels)
    return game


@pytest.fixture
def game_create_data(
    court_thailand,
    game_levels_light,
    game_levels_medium,
    payment_account_revolut
):
    return {
            'court_id': court_thailand.id,
            'message': 'Hi! Just old',
            'start_time': '2026-07-01T14:30:00Z',
            'end_time': '2026-07-01T16:30:00Z',
            'gender': 'MEN',
            'levels': [game_levels_light.name,
                       game_levels_medium.name],
            'is_private': False,
            'maximum_players': 5,
            'price_per_person': '5.00',
            'payment_type': payment_account_revolut.payment_type,
            'players': []
        }
