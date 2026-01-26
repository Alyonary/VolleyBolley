from random import sample

import pytest
from django.utils import timezone

from apps.core.models import DailyStats
from apps.core.task import (
    collect_full_project_stats,
    collect_stats_for_day,
)
from apps.event.models import Game, Tourney
from apps.players.models import Player


def get_unique_obj_create_dates() -> list[timezone.datetime]:
    """
    Helper function to get unique creation dates from a model.
    """
    game_dates = set(Game.objects.values_list('created_at__date', flat=True))
    player_dates = set(
        Player.objects.values_list('user__date_joined__date', flat=True)
    )
    tourney_dates = set(
        Tourney.objects.values_list('created_at__date', flat=True)
    )
    return sorted(
        [
            d
            for d in (game_dates | player_dates | tourney_dates)
            if d is not None
        ]
    )


@pytest.mark.django_db
def test_stats_created_for_all_unique_days(
    five_games_last_month, user_joined_bulk
):
    """
    Test that daily stats are created for all unique days
    on which games were created or users joined.
    """
    all_dates = get_unique_obj_create_dates()
    collect_full_project_stats()
    stats_dates = set(DailyStats.objects.values_list('date', flat=True))
    assert set(all_dates) == stats_dates


@pytest.mark.django_db
def test_dailystats_values_match_source_data(
    five_games_last_month, user_joined_bulk
):
    """
    Test that the values in DailyStats match the actual counts
    from Player and Game models for sampled days.
    """
    all_dates = get_unique_obj_create_dates()
    collect_full_project_stats()
    for day in sample(all_dates, min(1, len(all_dates))):
        stats = DailyStats.objects.get(date=day)
        players_count = Player.objects.filter(
            user__date_joined__date=day
        ).count()
        games_count = Game.objects.filter(created_at__date=day).count()
        assert stats.players_registered == players_count
        assert stats.games_created == games_count


@pytest.mark.django_db
def test_stats_collection_for_day(five_games_last_month, user_joined_bulk):
    """
    Test the collect_stats_for_day function for individual days.
    """
    all_dates = get_unique_obj_create_dates()
    for day in sample(all_dates, min(1, len(all_dates))):
        DailyStats.objects.filter(date=day).delete()
        result = collect_stats_for_day(day)
        assert result['status'] is True
        assert DailyStats.objects.filter(date=day).exists()
        ds = DailyStats.objects.get(date=day)
        expected_players = Player.objects.filter(
            user__date_joined__date=day
        ).count()
        expected_games = Game.objects.filter(created_at__date=day).count()
        excepted_tourneys = Tourney.objects.filter(
            created_at__date=day
        ).count()
        assert ds.players_registered == expected_players
        assert ds.games_created == expected_games
        assert ds.tourneys_created == excepted_tourneys
