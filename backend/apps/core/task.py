import logging

from celery import shared_task

from apps.notifications.constants import MAX_RETRIES, RETRY_PUSH_TIME

logger = logging.getLogger(__name__)


@shared_task
def collect_daily_stats(
    bind=True, max_retries=MAX_RETRIES, default_retry_delay=RETRY_PUSH_TIME
):
    """Collects daily statistics for the dashboard.
    This task aggregates data such as number of players registered,
    games created, and tournaments created for the current day.
    """
    pass
    # try:
    #     today = timezone.now().date()
    #     players_registered = Player.objects.filter(
    #         user__date_joined__date=today
    #     ).count()
    #     games_created = Game.objects.filter(
    #         end_time__date=today, is_active=False
    #     ).count()
    #     tourneys_created = Tourney.objects.filter(
    #         start_time__date=today, is_active=False
    #     ).count()
    #     DailyStats.objects.update_or_create(
    #         date=today,
    #         defaults={
    #             'players_registered': players_registered,
    #             'games_played': games_created,
    #             'tourneys_played': tourneys_created,
    #         },
    #     )
    #     logger.info(
    #         f'Daily stats collected for {today}: '
    #         f'{players_registered} players, {games_created} games, '
    #         f'{tourneys_created} tourneys.'
    #     )
    # except Exception as e:
    #     logger.error(f'Error collecting daily stats: {str(e)}')
    #     raise e


def collect_full_stats():
    """
    Collects full statistics for all days.
    This function aggregates data such as number of players registered,
    games created, and tournaments created for each day present in the data.
    """
    pass
    # player_dates = Player.objects.values_list(
    #     'user__date_joined__date', flat=True
    # ).distinct()
    # game_dates = Game.objects.values_list(
    #     'created_at__date', flat=True
    # ).distinct()
    # tourney_dates = Tourney.objects.values_list(
    #     'created_at__date', flat=True
    # ).distinct()
    # print(
    #     'Player dates:',
    #     player_dates,
    #     'Game dates:',
    #     game_dates,
    #     'Tourney dates:',
    #     tourney_dates,
    # )
    # all_dates = set(player_dates) | set(game_dates) | set(tourney_dates)
    # all_dates = sorted([d for d in all_dates if d is not None])

    # for day in all_dates:
    #     players_registered = Player.objects.stats_for_day(day)
    #     games_created = Game.objects.stats_for_day(day)
    #     tourneys_created = Tourney.objects.stats_for_day(day)
    #     DailyStats.objects.update_or_create(
    #         date=day,
    #         defaults={
    #             'players_registered': players_registered,
    #             'games_created': games_created,
    #             'tourneys_created': tourneys_created,
    #         },
    #     )
