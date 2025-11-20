from datetime import timedelta

import pytest
from django.utils import timezone

from apps.event.models import Tourney


@pytest.fixture
def tourney_data(
    bulk_create_registered_players,
    currency_type_thailand,
    court_thailand,
    payment_account_revolut,
    game_levels_light,
    game_levels_medium,
    player_thailand,
):
    """
    Return data for creating a tourney.
    The tourney is created in Thailand with 5 registered players.
    """
    start_time = timezone.now() + timedelta(days=2)
    end_time = start_time + timedelta(hours=6)

    return {
        'court_id': court_thailand.id,
        'message': 'Test tourney in Thailand',
        'start_time': start_time,
        'end_time': end_time,
        'gender': 'MEN',
        'player_levels': [game_levels_light, game_levels_medium],
        'is_private': False,
        'max_players': 16,
        'price_per_person': '10.00',
        'payment_type': payment_account_revolut.payment_type,
        'players': bulk_create_registered_players,
        'host': player_thailand,
        'currency_type': currency_type_thailand,
        'payment_account': payment_account_revolut.payment_account,
    }


@pytest.fixture
def tourney_thailand(tourney_data):
    working_data = tourney_data.copy()
    working_data.pop('players')
    levels = working_data.pop('player_levels')
    tourney = Tourney.objects.create(**working_data)
    tourney.player_levels.set(levels)
    return tourney


@pytest.fixture
def tourney_thailand_with_players(tourney_data):
    working_data = tourney_data.copy()
    players = working_data.pop('players')
    levels = working_data.pop('player_levels')
    tourney = Tourney.objects.create(**working_data)
    tourney.players.set(players)
    tourney.player_levels.set(levels)
    return tourney


@pytest.fixture
def ended_tourney(player_thailand, bulk_create_registered_players):
    """Create a tourney that has ended."""
    tourney = Tourney.objects.create(
        host=player_thailand,
        start_time=timezone.now() - timedelta(hours=3),
        end_time=timezone.now() - timedelta(hours=1),
        is_active=True,
        max_players=8,
        message='Ended tourney for testing',
    )
    tourney.players.set(bulk_create_registered_players[:3])
    return tourney


@pytest.fixture
def tourney_for_args(tourney_thailand):
    return (tourney_thailand.id,)
