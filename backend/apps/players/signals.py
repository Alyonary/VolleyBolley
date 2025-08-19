# signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.players.constants import BASE_PAYMENT_DATA
from apps.players.models import Payment, Player


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
