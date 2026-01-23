from copy import deepcopy
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from apps.event.models import Game
from apps.locations.models import City, Country
from apps.players.constants import Grades
from apps.players.models import Payment, Player

User = get_user_model()


@pytest.fixture
def country_thailand():
    return Country.objects.get_or_create(name='Thailand')[0]


@pytest.fixture
def city_in_thailand(country_thailand):
    return City.objects.get_or_create(
        name='Bangkok', country=country_thailand
    )[0]


@pytest.fixture
def country_cyprus():
    return Country.objects.get_or_create(name='Cyprus')[0]


@pytest.fixture
def city_in_cyprus(country_cyprus):
    return City.objects.get_or_create(name='Limassol', country=country_cyprus)[
        0
    ]


@pytest.fixture
def game_data(
    bulk_create_registered_players,
    currency_type_thailand,
    court_thailand,
    payment_account_revolut,
    game_levels_light,
    game_levels_medium,
    player_thailand,
):
    """
    Return data for creating a game.
    The game is created in Thailand with 5 registered players.
    """
    start_time = timezone.now() + timedelta(days=2)
    end_time = start_time + timedelta(hours=3)

    return {
        'court_id': court_thailand.id,
        'message': 'Test game in Thailand',
        'start_time': start_time,
        'end_time': end_time,
        'gender': 'MEN',
        'player_levels': [game_levels_light, game_levels_medium],
        'is_private': False,
        'max_players': 5,
        'price_per_person': '5.00',
        'payment_type': payment_account_revolut.payment_type,
        'players': bulk_create_registered_players,
        'host': player_thailand,
        'currency_type': currency_type_thailand,
        'payment_account': payment_account_revolut.payment_account,
    }


@pytest.fixture
def game_data_past(game_data):
    start_time = timezone.now() - timedelta(days=2)
    end_time = start_time + timedelta(hours=3)
    new_game_data = deepcopy(game_data)
    new_game_data.update({'start_time': start_time, 'end_time': end_time})
    return new_game_data


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
def archived_game_thailand(game_thailand_with_players):
    game = game_thailand_with_players
    game.end_time = timezone.now() - timedelta(days=1)
    game.is_active = False
    game.save()
    return game


@pytest.fixture
def game_thailand_with_players_past(game_data_past):
    working_data = game_data_past.copy()
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
    return APIClient()


@pytest.fixture
def api_client_thailand(active_user, client):
    client.force_authenticate(active_user)
    return client


@pytest.fixture
def another_user():
    return User.objects.create(
        first_name='Test user for Cyprus 1',
        last_name='Test user for Cyprus 1',
        username='Test user for Cyprus 1',
        email='test4@cyprus.com',
        password='test4@cyprus.com',
    )


@pytest.fixture
def player_thailand(active_user, country_thailand, city_in_thailand):
    return Player.objects.create(
        user=active_user,
        gender='MALE',
        country=country_thailand,
        city=city_in_thailand,
        is_registered=True,
    )


@pytest.fixture
def payment_account_revolut(player_thailand):
    return Payment.objects.create(
        player=player_thailand,
        payment_type='REVOLUT',
        payment_account='test acc',
    )


@pytest.fixture
def player_cyprus(another_user, country_cyprus, city_in_cyprus):
    return Player.objects.create(
        user=another_user,
        gender='MALE',
        country=country_cyprus,
        city=city_in_cyprus,
        is_registered=True,
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
    payment_account_revolut,
):
    start_time = timezone.now() + timedelta(days=2)
    end_time = start_time + timedelta(hours=2)

    return {
        'court_id': court_thailand.id,
        'message': 'Hi! Just old',
        'start_time': start_time.isoformat().replace('+00:00', 'Z'),
        'end_time': end_time.isoformat().replace('+00:00', 'Z'),
        'gender': 'MEN',
        'levels': [game_levels_light.name, game_levels_medium.name],
        'is_private': False,
        'maximum_players': 5,
        'price_per_person': '5.00',
        'payment_type': payment_account_revolut.payment_type,
        'players': [],
    }


@pytest.fixture
def player_thailand_female_pro(country_thailand):
    user = User.objects.create(
        first_name='Test user for games 1',
        last_name='Test user for games 1',
        username='Test user for games 1',
        email='test4@games.com',
        password='test4@games.com',
        phone_number='+82648129229',
    )
    player = Player.objects.create(
        user=user,
        gender='FEMALE',
        country=country_thailand,
        is_registered=True,
    )
    player.rating.grade = Grades.PRO.value
    player.rating.save()
    return player


@pytest.fixture
def api_client_thailand_pro(player_thailand_female_pro, client):
    client.force_authenticate(player_thailand_female_pro.user)
    return client


@pytest.fixture
def three_games_thailand(game_data):
    """Create three games in Thailand with same configuration."""
    games = []
    for i in range(3):
        working_data = game_data.copy()
        working_data['message'] = f'Test game {i + 1} in Thailand'
        players = working_data.pop('players')
        levels = working_data.pop('player_levels')

        start_time = working_data['start_time'] + timedelta(hours=i*4)
        end_time = working_data['end_time'] + timedelta(hours=i*4)
        working_data['start_time'] = start_time
        working_data['end_time'] = end_time

        game = Game.objects.create(**working_data)
        game.players.set(players)
        game.player_levels.set(levels)
        games.append(game)

    return games
