from datetime import timedelta

import pytest
from django.utils import timezone

from apps.event.models import Tourney


@pytest.fixture
def base_tourney_data(
    currency_type_thailand,
    court_thailand,
    payment_account_revolut,
    game_levels_light,
    game_levels_medium,
    player_thailand,
):
    """
    Return data for creating a tourney.
    """
    start_time = timezone.now() + timedelta(days=2)
    end_time = start_time + timedelta(hours=6)

    return {
        'court_id': court_thailand.id,
        'message': 'Test tourney in Thailand',
        'start_time': start_time,
        'end_time': end_time,
        'gender': 'MEN',
        'player_levels': [
            game_levels_light,
            game_levels_medium
        ],
        'price_per_person': '10.00',
        'payment_type': payment_account_revolut.payment_type,
        'host': player_thailand,
        'currency_type': currency_type_thailand,
        'payment_account': payment_account_revolut.payment_account,
    }


@pytest.fixture
def tourney_data_individual(base_tourney_data):
    individual_data = {
        "is_individual": True,
        "max_players": 5,
        "maximum_teams": 1
    }
    return individual_data | base_tourney_data


@pytest.fixture
def tourney_data_team(base_tourney_data):
    team_data = {
        "is_individual": False,
        "max_players": 8,
        "maximum_teams": 4
    }
    return team_data | base_tourney_data


@pytest.fixture
def tourney_thai_ind(tourney_data_individual):
    working_data = tourney_data_individual.copy()
    levels = working_data.pop('player_levels')
    tourney = Tourney.objects.create(**working_data)
    tourney.player_levels.set(levels)
    return tourney


@pytest.fixture
def tourney_thai_team(tourney_data_team):
    working_data = tourney_data_team.copy()
    levels = working_data.pop('player_levels')
    tourney = Tourney.objects.create(**working_data)
    tourney.player_levels.set(levels)
    return tourney


@pytest.fixture
def create_custom_tourney(tourney_data_individual):
    # working_data = tourney_data_individual.copy()

    def _create(**kwargs):
        for key, value in kwargs.items():
            if tourney_data_individual.get(key, None):
                tourney_data_individual[key] = value
        levels = tourney_data_individual.pop('player_levels')
        tourney = Tourney.objects.create(**tourney_data_individual)
        tourney.player_levels.set(levels)
        tourney_data_individual['player_levels'] = levels
        return tourney
    return _create


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
