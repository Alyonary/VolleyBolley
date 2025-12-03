from django.apps import AppConfig

# from django.db.models.signals import post_save


class EventConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.event'

    def ready(self):
        from apps.event import signals # noqa
