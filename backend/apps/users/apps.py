import threading

from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.users'
    _initialized = False

    def ready(self):
        if self._initialized:
            return

        from .utils import (
            create_superuser_with_settings_check,
            wait_for_django_ready,
        )

        def initialize():
            """Start superuser auto creation pipeline."""
            if wait_for_django_ready():
                create_superuser_with_settings_check()

        # Create superuser in a separate thread 
        thread = threading.Thread(target=initialize, daemon=True)
        thread.start()

        self._initialized = True
