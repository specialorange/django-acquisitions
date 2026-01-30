from django.apps import AppConfig


class AcquisitionsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "acquisitions"
    verbose_name = "Customer Acquisitions"

    def ready(self):
        # Import signals when app is ready
        try:
            from . import signals  # noqa: F401
        except ImportError:
            pass
