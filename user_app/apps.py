from django.apps import AppConfig


class UserAppConfig(AppConfig):
    name = 'user_app'

    def ready(self):
        import user_app.signals  # noqa: F401 — registers the post_save signal
