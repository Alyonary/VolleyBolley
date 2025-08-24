from apps.notifications.push_service import PushService


def get_push_service():
    """Get an instance of PushService."""
    return PushService()