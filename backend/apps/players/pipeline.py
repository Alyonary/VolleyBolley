from typing import Dict, List

from backend.apps.players.constants import (
    BASE_PAYMENT_DATA,
    LocationEnums,
)

from apps.players.models import Payment, Player, PlayerLocation


def create_player(strategy, details, backend, user=None, *args, **kwargs):
    """Lounge a pipeline to create a player for a new user."""
    if user and not hasattr(user, 'player'):
        location, _ = PlayerLocation.objects.get_or_create(
            country=LocationEnums.DEFAULT_COUNTRY.value,
            city=LocationEnums.DEFAULT_CITY.value
        )
        player = Player.objects.create(
            user=user,
            location=location,
            is_registered=False
        )
        create_payments(player, BASE_PAYMENT_DATA)
    return None


def create_payments(player: Player, payment_data: List[Dict]) -> List[Payment]:
    """Create a list of standard payments for a new player."""
    for data in payment_data:
        data['player'] = player
    return Payment.objects.bulk_create(payment_data)
