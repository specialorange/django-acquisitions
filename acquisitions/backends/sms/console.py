"""
Console SMS backend for testing/development.

Prints SMS messages to the console instead of sending them.
"""

import logging
import uuid

from ..base import BaseSMSBackend, SendResult

logger = logging.getLogger(__name__)


class ConsoleBackend(BaseSMSBackend):
    """SMS backend that prints to console (for testing)."""

    def send_sms(
        self,
        to: str,
        body: str,
        from_number: str | None = None,
    ) -> SendResult:
        """Print SMS to console instead of sending."""
        is_valid, formatted_to = self.validate_phone_number(to)
        if not is_valid:
            return SendResult(success=False, error=formatted_to)

        message_id = str(uuid.uuid4())

        # Print to console
        print("=" * 60)
        print("SMS MESSAGE (Console Backend)")
        print("=" * 60)
        print(f"To: {formatted_to}")
        if from_number:
            print(f"From: {from_number}")
        print(f"Message ID: {message_id}")
        print("-" * 60)
        print(body)
        print("=" * 60)

        logger.info(f"Console SMS to {formatted_to}: {body[:50]}...")

        return SendResult(
            success=True,
            message_id=message_id,
            metadata={"to": formatted_to, "body_preview": body[:100]},
        )
