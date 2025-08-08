from typing import Dict, List

from apps.players.constants import (
    BASE_PAYMENT_DATA,
)
from apps.players.models import Payment, Player


def create_player(strategy, details, backend, user=None, *args, **kwargs):
    """Lounge a pipeline to create a player for a new user."""
    _get_or_create_player(user, BASE_PAYMENT_DATA)
    return None


def _get_or_create_player(user, payment_data):
    player, created = Player.objects.get_or_create(
            user=user
        )
    if created:
        _create_payments(player, payment_data)


def _create_payments(
    player: Player, payment_data: List[Dict]
) -> List[Payment]:
    """Create a list of standard payments for a new player."""
    payments = []
    for data in payment_data:
        # Create a Payment instance for each dictionary
        payment = Payment(
            player=player,
            payment_type=data['payment_type'],
            payment_account=data['payment_account'],
            is_preferred=data['is_preferred']
        )
        payments.append(payment)
    return Payment.objects.bulk_create(payments)
