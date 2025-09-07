from celery import shared_task

from apps.players.rating import PlayerLevelGrade


@shared_task
def downgrade_inactive_players_task():
    PlayerLevelGrade.downgrade_inactive_players(days=90)

@shared_task
def update_players_rating_task():
    PlayerLevelGrade.update_players_rating()