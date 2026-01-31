"""
Test settings for django-acquisitions.

Minimal Django configuration for testing.
"""

SECRET_KEY = "test-secret-key-for-acquisitions"  # pragma: allowlist secret

DEBUG = True

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "rest_framework",
    "acquisitions",
]

ROOT_URLCONF = "tests.urls"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

USE_TZ = True
TIME_ZONE = "UTC"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {},
    },
]

# Acquisitions settings for testing
ACQUISITIONS_USE_CELERY = False  # Disable Celery in tests
ACQUISITIONS_EMAIL_BACKEND = "acquisitions.backends.email.django_email.DjangoEmailBackend"
ACQUISITIONS_SMS_BACKEND = "acquisitions.backends.sms.console.ConsoleBackend"

# Django email backend for testing
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
DEFAULT_FROM_EMAIL = "test@example.com"
