from django.db.models.signals import post_migrate
from django.dispatch import receiver

from apps.users.utils import create_superuser_with_settings_check


@receiver(post_migrate)
def create_superuser_after_migrate(sender, **kwargs):
    """Create a superuser after migrations are applied."""
    create_superuser_with_settings_check()
