import logging
import os
import time

from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import connection

logger = logging.getLogger(__name__)

User = get_user_model()

username: str | None = os.getenv('DJANGO_SUPERUSER_USERNAME', None)
first_name: str | None = os.getenv('DJANGO_SUPERUSER_FIRST_NAME', None)
last_name: str | None = os.getenv('DJANGO_SUPERUSER_LAST_NAME', None)
password: str | None = os.getenv('DJANGO_SUPERUSER_PASSWORD', None)


def is_django_fully_ready() -> bool:
    """Comprehensive health check for Django application readiness.

    Performs a series of critical checks to ensure Django is completely
    initialized and ready for database operations.
    This includes verifying that all applications are loaded,
    models are available, database connection is established,
    and essential database table (the User table) exists.

    This function is designed to be used during application startup or by
    background processes that need guaranteed Django readiness before
    performing database operations like creating superusers.

    Returns:
        bool: True if all readiness checks pass,
              indicating Django is fully operational.

    Raises:
        Exception: With descriptive message if any readiness check fails:
            - If Django applications haven't finished loading
            - If model registry isn't properly initialized
            - If database connection cannot be established
            - If the User table doesn't exist in database
            - If using a non-PostgreSQL database
    """
    apps_ready = apps.ready
    models_ready = hasattr(apps, 'get_models') and callable(apps.get_models)
    db_connection = connection.ensure_connection

    if not apps_ready:
        raise Exception('Apps are not ready.')

    if not models_ready:
        raise Exception('Models are not ready.')

    if not db_connection:
        raise Exception('Connection failed.')

    try:
        with connection.cursor() as cursor:
            if connection.vendor == 'postgresql':
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_name = %s
                    );
                """, [User._meta.db_table])
                exists = cursor.fetchone()[0]

                if not exists:
                    err_msg = "There isn't user table in the database."
                    logger.error(err_msg)

                    raise Exception(err_msg)

                logger.debug('connection is successful.')

                return True

            err_msg = 'You are probably using not PostgreSQL database.'
            logger.error(err_msg)

            raise Exception(err_msg)

    except Exception as e:
        logger.debug(f'Error: {e}. Connection failed.')

        raise e


def wait_for_django_ready(max_retries: int = 10, delay: int = 1) -> bool:
    """Wait for Django and Database to be fully initialized.

    This function periodically checks if Django has completed
    its initialization process and is ready to perform database operations.
    It's particularly useful for background tasks that need to ensure
    Django is fully set up before attempting to interact
    with the database or models.

    The function will retry the readiness check multiple times
    with configurable delays between attempts, making it robust for scenarios
    where Django might be initializing concurrently with other processes.

    Args:
        max_retries: Maximum number of readiness check attempts.
                     Defaults to 10 attempts.
        delay: Time in seconds to wait between each retry attempt.
               Defaults to 1 second.

    Returns:
        bool: True if Django becomes ready within the retry limit,
              False if maximum retries are exceeded without success.

    Raises:
        This function catches all exceptions internally and will return False
        rather than propagating exceptions.

    Note:
        This function is designed to be called from background threads or
        during application startup where Django initialization might not
        be complete.
    """
    for i in range(max_retries):
        try:
            is_django_fully_ready()
            logger.info("✅ Django is fully ready")

            return True

        except Exception as e:
            logger.error(f'Django is not ready: {e}')

            if i < max_retries - 1:
                logger.debug(f"⏳ Waiting for Django... ({i+1}/{max_retries})")
                time.sleep(delay)

            continue

    logger.error("⚠️ Django is not fully ready.")

    return False


def create_superuser_with_settings_check(
    username: str | None = username,
    first_name: str | None = first_name,
    last_name: str | None = last_name,
    password: str | None = password
) -> None:
    """Create a superuser automatically.

    This function attempts to create a Django superuser using credentials from
    environment variables, but only if specific conditions are met.

    The creation process will be skipped if:
    - AUTO_CREATE_DEFAULT_SUPERUSER setting is False
    - Any superuser already exists in the database
    - The requested username is already taken by another user
    - Required environment variables are missing or empty

    Args:
        username: Superuser username from
                DJANGO_SUPERUSER_USERNAME env variable
        first_name: Superuser first name from
                DJANGO_SUPERUSER_FIRST_NAME env variable
        last_name: Superuser last name from
                DJANGO_SUPERUSER_LAST_NAME env variable
        password: Superuser password from
                DJANGO_SUPERUSER_PASSWORD env variable

    Returns: None

    Raises:
        django.db.DatabaseError: If database operations fail
        Exception: For unexpected errors during user creation

    Side Effects:
        - Creates a superuser in the database if all conditions are met
        - Writes log messages at appropriate levels (INFO, WARNING, ERROR)
        - Modifies the User table by adding a new superuser record

    Note:
        Environment variables should be set before calling this function:
        - DJANGO_SUPERUSER_USERNAME
        - DJANGO_SUPERUSER_FIRST_NAME
        - DJANGO_SUPERUSER_LAST_NAME
        - DJANGO_SUPERUSER_PASSWORD

        Also ensure AUTO_CREATE_DEFAULT_SUPERUSER is True.
    """
    if not getattr(settings, 'AUTO_CREATE_DEFAULT_SUPERUSER', False):
        logger.warning(
            'Pass the superuser auto creation process: '
            'AUTO_CREATE_DEFAULT_SUPERUSER = False.'
        )

        return

    if (
        User.objects.filter(is_superuser=True).exists() and
        not getattr(settings, 'MANY_SUPERUSERS', False)
    ):
        logger.info(
            'Pass the superuser auto creation process: '
            f'superuser {username} has been already created previously. '
            'Set MANY_SUPERUSERS to True to allow auto creation '
            'of another superuser.'
        )

        return

    if User.objects.filter(username=username).exists():
        logger.error(
            'Superuser auto creation failed: '
            f'username {username} is already occupied by another user.'
        )

        return

    if all([username, first_name, last_name, password]):
        User.objects.create_superuser(
            username,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        logger.info(
            f'Superuser {username} has been successfully auto created.'
        )

        return

    logger.error(
        'Superuser auto creation failed: '
        f'username - {username}, first name - {first_name}, '
        f'last name - {last_name}, '
    )

    return
