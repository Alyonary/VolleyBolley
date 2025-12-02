import logging

from celery import shared_task
from django.utils import timezone

from apps.core.models import DailyStats
from apps.event.models import Game, Tourney
from apps.notifications.constants import MAX_RETRIES, RETRY_PUSH_TIME
from apps.players.models import Player

logger = logging.getLogger(__name__)


@shared_task
def collect_daily_stats(
    bind=True, max_retries=MAX_RETRIES, default_retry_delay=RETRY_PUSH_TIME
):
    """Collects daily statistics for the dashboard.
    This task aggregates data such as number of players registered,
    games created, and tournaments created for the current day.
    """
    try:
        today = timezone.now().date()
        players_registered = Player.objects.filter(
            user__date_joined__date=today
        ).count()
        games_created = Game.objects.filter(
            end_time__date=today, is_active=False
        ).count()
        tourneys_created = Tourney.objects.filter(
            start_time__date=today, is_active=False
        ).count()
        DailyStats.objects.update_or_create(
            date=today,
            defaults={
                'players_registered': players_registered,
                'games_played': games_created,
                'tourneys_played': tourneys_created,
            },
        )
        logger.info(
            f'Daily stats collected for {today}: '
            f'{players_registered} players, {games_created} games, '
            f'{tourneys_created} tourneys.'
        )
    except Exception as e:
        logger.error(f'Error collecting daily stats: {str(e)}')
        raise e
