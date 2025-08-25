import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from apps.event.models import Game

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
        'message': 'Test game',
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
def authored_APIClient(active_user, client):
    client.force_authenticate(active_user)
    return client


@pytest.fixture
def another_user(user_data):
    user_data['username'] = 'AnotherUser'
    user_data['phone_number'] = '88005555535'
    return User.objects.create_user(**user_data)


@pytest.fixture
def another_user_client(another_user, client):
    client.force_authenticate(another_user)
    return client
