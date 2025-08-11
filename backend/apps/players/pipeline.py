from apps.players.models import Player


def create_player(strategy, details, backend, user=None, *args, **kwargs):
    """Lounge a pipeline to create a player for a new user."""
    if user:
        Player.objects.get_or_create(user=user)
    return None
