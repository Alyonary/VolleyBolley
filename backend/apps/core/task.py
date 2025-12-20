import logging

from celery import shared_task

from apps.core.models import DailyStats
from apps.event.models import Game, Tourney
from apps.notifications.constants import MAX_RETRIES, RETRY_PUSH_TIME
from apps.players.models import Player

logger = logging.getLogger(__name__)


@shared_task(max_retries=MAX_RETRIES, default_retry_delay=RETRY_PUSH_TIME)
def collect_full_stats():
    """
    Collects full statistics for all days.
    This function aggregates data such as number of players registered,
    games created, and tournaments created for each day present in the data.
    """
    player_dates = Player.objects.values_list(
        'user__date_joined__date', flat=True
    ).distinct()
    game_dates = Game.objects.values_list(
        'created_at__date', flat=True
    ).distinct()
    tourney_dates = Tourney.objects.values_list(
        'created_at__date', flat=True
    ).distinct()
    all_dates = set(player_dates) | set(game_dates) | set(tourney_dates)
    all_dates = sorted([d for d in all_dates if d is not None])
    for day in all_dates:
        players_registered = Player.objects.stats_for_day(day)
        games_created = Game.objects.stats_for_day(day)
        tourneys_created = Tourney.objects.stats_for_day(day)
        if not DailyStats.objects.filter(date=day).exists():
            DailyStats.objects.create(
                date=day,
                players_registered=players_registered,
                games_created=games_created,
                tourneys_created=tourneys_created,
            )
