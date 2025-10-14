# signals.py
import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.players.constants import (
    BASE_PAYMENT_DATA,
    PlayerStrEnums,
)
from apps.players.models import Payment, Player, PlayerRating, PlayerRatingVote
from apps.players.rating import GradeSystem

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Player)
def init_player_payments(sender, instance, created, **kwargs):
    """Create a list of standard payments for a new player."""
    if created:
        Payment.objects.bulk_create([
            Payment(
                player=instance,
                payment_type=data['payment_type'],
                payment_account=data['payment_account'],
                is_preferred=data['is_preferred']
            )
            for data in BASE_PAYMENT_DATA
        ])


@receiver(post_save, sender=Player)
def create_player_rating_obj(sender, instance, created, **kwargs):
    """
    Signal to create PlayerRating when a new Player is created.
    Sets grade from Player instance or defaults.
    """
    if created:
        PlayerRating.objects.create(
            player=instance,
            grade=getattr(
                instance,
                'level',
                PlayerStrEnums.DEFAULT_GRADE.value
            ),
        )


@receiver(post_save, sender=PlayerRatingVote)
def update_player_rating_on_vote(sender, instance, created, **kwargs):
    """
    Signal to update PlayerRating when a new PlayerRatingVote is created.
    Simple synchronous execution.
    """
    if created:
        try:
            status = GradeSystem.update_player_rating(
                player=instance.rated,
                vote=instance
            )
            logger.info(f"Player id={instance.rated.id} rating {status}")
        except Exception as e:
            logger.error(f"Error updating player rating: {e}")
