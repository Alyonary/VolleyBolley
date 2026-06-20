import logging

from celery import shared_task
from django.utils import timezone

from apps.core.constants import PREVIOUS_DAY_OFFSET
from apps.core.models import DailyStats
from apps.event.models import Game, Tourney
from apps.notifications.constants import MAX_RETRIES, RETRY_PUSH_TIME
from apps.players.models import Player

logger = logging.getLogger(__name__)


@shared_task(max_retries=MAX_RETRIES, default_retry_delay=RETRY_PUSH_TIME)
def collect_full_stats_task():
    """
    Collects full statistics for all days.
    This function aggregates data such as number of players registered,
    games created, and tournaments created for each day present in the data.
    """
    logger.info('Starting full project stats collection task.')
    collect_full_project_stats()
    return True


@shared_task(max_retries=MAX_RETRIES, default_retry_delay=RETRY_PUSH_TIME)
def collect_stats_for_previous_day_task():
    """
    Collects statistics for a specific day.
    This function aggregates data such as number of players registered,
    games created, and tournaments created for the previous day
    """
    previous_day = timezone.now().date() - timezone.timedelta(
        days=PREVIOUS_DAY_OFFSET
    )
    logger.info(f'Starting stats collection for day: {previous_day}.')
    return collect_stats_for_day(previous_day)


def collect_stats_for_day(day):
    """
    Collects statistics for a specific day.
    This function aggregates data such as number of players registered,
    games created, and tournaments created for the specified day.
    """
    try:
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
        return {'status': True, 'message': 'Stats collected successfully'}
    except Exception as e:
        logger.error(f'Error collecting stats for day {day}: {e}')
        return {'status': False, 'message': str(e)}


def collect_full_project_stats():
    """
    Helper function to collect stats for all days.
    This function retrieves all unique days from the Player, Game,
    and Tourney models and triggers the stats collection for each day.
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
    logger.info(f'Collecting stats for {len(all_dates)} days.')
    stats = {
        'success': 0,
        'failed': 0,
    }
    for day in all_dates:
        result = collect_stats_for_day(day)
        if not result['status']:
            stats['failed'] += 1
            logger.error(
                f'Failed to collect stats for day {day}: {result["message"]}'
            )
            continue
        stats['success'] += 1
    logger.info(
        f'Stats collection completed. Success: {stats["success"]}, '
        f'Failed: {stats["failed"]}'
    )
    return stats
