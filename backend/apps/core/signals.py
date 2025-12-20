from django.db import connection
from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver

from apps.core.models import FAQ
from apps.core.utils import initialize_faq


def table_exists(table_name: str) -> bool:
    """Check if a table exists in the database using ORM."""
    return table_name in connection.introspection.table_names()


@receiver(post_migrate)
def load_faq(sender, **kwargs):
    """Initialize FAQ data after migrations are applied."""
    if table_exists('core_faq'):
        initialize_faq()


@receiver(post_save, sender=FAQ)
def deactivate_other_faqs(sender, instance, **kwargs):
    """
    Ensure only one FAQ is active at a time.
    When an FAQ instance is saved and is marked as active,
    deactivate all other FAQ instances.
    """
    if instance.is_active:
        FAQ.objects.exclude(id=instance.id).update(is_active=False)
