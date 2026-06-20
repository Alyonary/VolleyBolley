from datetime import timedelta
from random import randint

import pytest
from django.utils import timezone

from apps.event.models import Game
from apps.players.models import Player


@pytest.fixture
def five_games_last_month(game_data):
    """
    Создаёт 5 игр, каждая с уникальной датой в пределах последнего месяца.
    """
    games = []
    base_date = timezone.now() - timedelta(days=25)
    for i in range(5):
        working_data = game_data.copy()
        players = working_data.pop('players')
        levels = working_data.pop('player_levels')
        # Дата старта и окончания игры
        start_time = base_date + timedelta(days=i * 5, hours=10)
        end_time = start_time + timedelta(hours=3)
        working_data['start_time'] = start_time
        working_data['end_time'] = end_time
        game = Game.objects.create(
            **working_data, created_at=start_time - timedelta(hours=1)
        )
        game.players.set(players)
        game.player_levels.set(levels)
        games.append(game)
    return games


@pytest.fixture
def user_joined_bulk(django_user_model):
    today = timezone.now().date()
    for i in range(10):
        user = django_user_model.objects.create_user(
            username=f'user{i}',
            password='pass',
            date_joined=today - timedelta(days=randint(0, 30)),
        )
        Player.objects.create(user=user)
