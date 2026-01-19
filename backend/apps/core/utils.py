import logging

from django.db import connection, transaction

from apps.admin_panel.services import FileUploadService
from apps.core.constants import DEFAULT_FAQ
from apps.core.models import FAQ
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
        return

    content = FileUploadService().download_file_by_path(file_path)

    with transaction.atomic():
        if not FAQ.objects.filter(name=DEFAULT_FAQ).exists():
            FAQ.objects.create(
                content=content, is_active=True, name=DEFAULT_FAQ
            )
            logger.info('Created default FAQ.')
            return
    logger.info('FAQ already exists. No action taken.')


def initialize_faq() -> None:
    if not check_is_db_table_exists(FAQ._meta.db_table):
        logger.warning(
            'FAQ table does not exist. Skipping FAQ initialization.'
        )
        return
    filename = f'{DEFAULT_FAQ}.md'
    faq_file_path = BASE_DIR / 'data' / filename
    try:
        load_faq_from_file(faq_file_path)
    except FileNotFoundError:
        logger.error('Faq file not found:')
        return
