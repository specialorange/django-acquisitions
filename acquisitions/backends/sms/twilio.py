"""
Twilio SMS backend.

Requires: pip install django-acquisitions[twilio]
"""

import logging

from ..base import BaseSMSBackend, SendResult
from ...settings import acquisitions_settings

logger = logging.getLogger(__name__)


class TwilioBackend(BaseSMSBackend):
    """Twilio SMS backend."""

    def __init__(self):
        self._client = None

    @property
    def client(self):
        """Lazy-load Twilio client."""
        if self._client is None:
            try:
                from twilio.rest import Client
            except ImportError as e:
                raise ImportError(
                    "Twilio is not installed. Install with: pip install django-acquisitions[twilio]"
                ) from e

            account_sid = acquisitions_settings.TWILIO_ACCOUNT_SID
            auth_token = acquisitions_settings.TWILIO_AUTH_TOKEN

            if not account_sid or not auth_token:
                raise ValueError(
                    "Twilio credentials not configured. "
                    "Set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN in settings."
                )

            self._client = Client(account_sid, auth_token)
        return self._client

    def send_sms(
        self,
        to: str,
        body: str,
        from_number: str | None = None,
    ) -> SendResult:
        """Send SMS via Twilio."""
        try:
            from_num = from_number or acquisitions_settings.TWILIO_FROM_NUMBER
            if not from_num:
                return SendResult(
                    success=False,
                    error="No from_number configured. Set TWILIO_FROM_NUMBER in settings.",
                )

            is_valid, formatted_to = self.validate_phone_number(to)
            if not is_valid:
                return SendResult(success=False, error=formatted_to)

            message = self.client.messages.create(
                to=formatted_to,
                from_=from_num,
                body=body,
            )

            logger.info(f"SMS sent to {to}: SID={message.sid}")

            return SendResult(
                success=True,
                message_id=message.sid,
                metadata={"status": message.status},
            )

        except Exception as e:
            logger.exception(f"Failed to send SMS to {to}")
            return SendResult(success=False, error=str(e))
