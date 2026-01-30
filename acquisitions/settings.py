"""
App settings for django-acquisitions.

Override in your project's settings.py with the ACQUISITIONS_ prefix.
"""

from django.conf import settings


class AcquisitionsSettings:
    """
    Settings for django-acquisitions.

    Override in your settings.py:
        ACQUISITIONS_TENANT_MODEL = 'accounts.Account'  # MST
        ACQUISITIONS_EMAIL_BACKEND = 'acquisitions.backends.email.gmail_api.GmailBackend'
        ACQUISITIONS_SMS_BACKEND = 'acquisitions.backends.sms.twilio.TwilioBackend'
    """

    @property
    def TENANT_MODEL(self):
        """
        Tenant model for multi-tenant support.

        None = MFT (schema isolation)
        'app.Model' = MST (FK to account)
        """
        return getattr(settings, "ACQUISITIONS_TENANT_MODEL", None)

    @property
    def TENANT_FIELD_NAME(self):
        """Field name for tenant FK on models."""
        return getattr(settings, "ACQUISITIONS_TENANT_FIELD_NAME", "account")

    @property
    def EMAIL_BACKEND(self):
        """Email backend class path."""
        return getattr(
            settings,
            "ACQUISITIONS_EMAIL_BACKEND",
            "acquisitions.backends.email.django_email.DjangoEmailBackend",
        )

    @property
    def SMS_BACKEND(self):
        """SMS backend class path."""
        return getattr(
            settings,
            "ACQUISITIONS_SMS_BACKEND",
            "acquisitions.backends.sms.console.ConsoleBackend",
        )

    @property
    def TWILIO_ACCOUNT_SID(self):
        """Twilio Account SID."""
        return getattr(settings, "TWILIO_ACCOUNT_SID", None)

    @property
    def TWILIO_AUTH_TOKEN(self):
        """Twilio Auth Token."""
        return getattr(settings, "TWILIO_AUTH_TOKEN", None)

    @property
    def TWILIO_FROM_NUMBER(self):
        """Twilio From Number."""
        return getattr(settings, "TWILIO_FROM_NUMBER", None)

    @property
    def USE_CELERY(self):
        """
        Whether to use Celery for async tasks.

        Defaults to False - set to True if Celery is installed and configured.
        When False, tasks run synchronously.
        """
        return getattr(settings, "ACQUISITIONS_USE_CELERY", False)

    @property
    def CELERY_QUEUE(self):
        """Celery queue name for acquisitions tasks."""
        return getattr(settings, "ACQUISITIONS_CELERY_QUEUE", "default")

    @property
    def MAX_EMAILS_PER_HOUR(self):
        """Rate limit for emails per hour."""
        return getattr(settings, "ACQUISITIONS_MAX_EMAILS_PER_HOUR", 100)

    @property
    def MAX_SMS_PER_HOUR(self):
        """Rate limit for SMS per hour."""
        return getattr(settings, "ACQUISITIONS_MAX_SMS_PER_HOUR", 50)

    @property
    def ONBOARDING_CALLBACK(self):
        """
        Callback function path for lead-to-customer conversion.

        Should be a string like 'myapp.services.create_customer_from_lead'
        The function receives (lead, user) and should return {'success': bool, 'customer_id': ...}
        """
        return getattr(settings, "ACQUISITIONS_ONBOARDING_CALLBACK", None)

    @property
    def DEFAULT_FROM_EMAIL(self):
        """Default from email for outreach."""
        return getattr(settings, "ACQUISITIONS_DEFAULT_FROM_EMAIL", None) or getattr(
            settings, "DEFAULT_FROM_EMAIL", "noreply@example.com"
        )


acquisitions_settings = AcquisitionsSettings()
