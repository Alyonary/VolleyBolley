from celery import shared_task

from apps.players.rating import PlayerGradeLevel


@shared_task
def downgrade_inactive_players_task():
    PlayerGradeLevel.downgrade_inactive_players(days=60)

@shared_task
def update_players_rating_task():
    PlayerGradeLevel.update_players_rating()