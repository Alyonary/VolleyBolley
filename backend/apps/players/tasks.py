import logging

from celery import shared_task

from apps.notifications.constants import MAX_RETRIES, RETRY_PUSH_TIME
from apps.players.rating import GradeSystem

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=MAX_RETRIES,
    default_retry_delay=RETRY_PUSH_TIME
)
def downgrade_inactive_players_task(self):
    try:
        downgraded_count = GradeSystem.downgrade_inactive_players()
        logger.info(f"Downgraded {downgraded_count} inactive players.")
        return downgraded_count
    except Exception as e:
        logger.error(f"Error downgrading inactive players: {e}")
        raise self.retry(exc=e) from e


@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def update_players_rating_task(self):
    try:
        rate_update_stats = GradeSystem.bulk_update_players_rating()
        logger.info(f"Player ratings updated: {rate_update_stats}")
        return rate_update_stats
    except Exception as e:
        logger.error(f"Error updating player ratings: {e}")
        raise self.retry(exc=e) from e