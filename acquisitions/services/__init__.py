"""
Services for customer acquisition.
"""

from .communication import get_email_backend, get_sms_backend
from .onboarding import convert_prospective_client

__all__ = [
    "get_email_backend",
    "get_sms_backend",
    "convert_prospective_client",
]
