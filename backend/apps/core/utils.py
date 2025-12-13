import logging
import os
from datetime import timedelta

from django.db import connection, transaction

from apps.core.constants import DEFAULT_FAQ
from apps.core.models import FAQ, NotificationsTime
from volleybolley.settings import BASE_DIR

logger = logging.getLogger(__name__)


def check_is_db_table_exists(table_name: str) -> bool:
    """Check if a database table exists using ORM."""
    return table_name in connection.introspection.table_names()


def load_faq_from_file(file_path) -> bool:
    """
    Load FAQ content from a markdown file.
    Create an active FAQ entry in the database if none exists.
    """
    if not check_is_db_table_exists(FAQ._meta.db_table):
        logger.warning('FAQ table does not exist in the database.')
        return False

    if not os.path.exists(file_path):
        raise FileNotFoundError(f'FAQ file not found at {file_path}')

    with open(file_path, 'r', encoding='utf-8') as faq_file:
        content = faq_file.read()

    with transaction.atomic():
        if not FAQ.objects.filter(name=DEFAULT_FAQ).exists():
            faq = FAQ.objects.create(
                content=content,
                is_active=True,
                name=DEFAULT_FAQ
            )
            logger.info('Created default FAQ.')
            return True
    return False


def initialize_faq() -> None:
    filename = f'{DEFAULT_FAQ}.md'
    faq_file_path = BASE_DIR / 'data' / filename
    try:
        load_faq_from_file(faq_file_path)
    except FileNotFoundError:
        logger.error('Faq file not found:')
        return


def initialize_notification_time_settings() -> None:
    with transaction.atomic():
        if not NotificationsTime.objects.exists():
            NotificationsTime.objects.get_or_create(
                name='Develop Notification Time Settings',
                defaults={
                    'closed_event_notification': timedelta(minutes=2),
                    'pre_event_notification': timedelta(minutes=5),
                    'advance_notification': timedelta(minutes=10),
                    'is_active': True,
                },
            )
            NotificationsTime.objects.get_or_create(
                name='Production Notification Time Settings',
                defaults={
                    'closed_event_notification': timedelta(hours=1),
                    'pre_event_notification': timedelta(hours=1),
                    'advance_notification': timedelta(hours=24),
                    'is_active': False,
                },
            )
            logger.info('Initialized notification time settings.')
        else:
            logger.info('Notification time settings already initialized.')
