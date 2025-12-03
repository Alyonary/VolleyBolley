import logging
import os

from django.db import transaction

from apps.core.constants import DEFAULT_FAQ
from apps.core.models import FAQ
from volleybolley.settings import BASE_DIR

logger = logging.getLogger(__name__)


def load_faq_from_file(file_path) -> bool:
    """
    Load FAQ content from a markdown file.
    Create an active FAQ entry in the database if none exists.
    """

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"FAQ file not found at {file_path}")

    with open(file_path, "r", encoding="utf-8") as faq_file:
        content = faq_file.read()

    with transaction.atomic():
        if not FAQ.objects.filter(name=DEFAULT_FAQ).exists():
            faq = FAQ.objects.create(
                content=content,
                is_active=True,
                name=DEFAULT_FAQ
            )
            print(faq.content)
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
