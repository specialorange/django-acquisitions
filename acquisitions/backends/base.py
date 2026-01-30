"""
Abstract base classes for communication backends.

Projects implement these to integrate with their email/SMS systems.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class SendResult:
    """Result of a send operation."""

    success: bool
    message_id: str | None = None
    error: str | None = None
    metadata: dict | None = field(default_factory=dict)


class BaseEmailBackend(ABC):
    """Abstract base class for email backends."""

    @abstractmethod
    def send_email(
        self,
        to: str | list[str],
        subject: str,
        body_text: str,
        body_html: str | None = None,
        from_email: str | None = None,
        reply_to: str | None = None,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        attachments: list[dict] | None = None,
    ) -> SendResult:
        """
        Send an email.

        Args:
            to: Recipient email(s)
            subject: Email subject
            body_text: Plain text body
            body_html: Optional HTML body
            from_email: Sender email (uses default if not provided)
            reply_to: Reply-to address
            cc: CC recipients
            bcc: BCC recipients
            attachments: List of dicts with 'filename', 'content', 'mimetype'

        Returns:
            SendResult with success status and message_id or error
        """
        pass


class BaseSMSBackend(ABC):
    """Abstract base class for SMS backends."""

    @abstractmethod
    def send_sms(
        self,
        to: str,
        body: str,
        from_number: str | None = None,
    ) -> SendResult:
        """
        Send an SMS message.

        Args:
            to: Recipient phone number
            body: Message body
            from_number: Sender phone number (uses default if not provided)

        Returns:
            SendResult with success status and message_id or error
        """
        pass

    def validate_phone_number(self, phone: str) -> tuple[bool, str]:
        """
        Validate and format a phone number.

        Args:
            phone: Phone number to validate

        Returns:
            Tuple of (is_valid, formatted_number_or_error)
        """
        import re

        # Remove all non-digit characters
        digits = re.sub(r"\D", "", phone)

        # Handle US numbers
        if len(digits) == 10:
            return True, f"+1{digits}"
        elif len(digits) == 11 and digits[0] == "1":
            return True, f"+{digits}"
        elif len(digits) > 10 and phone.startswith("+"):
            return True, f"+{digits}"
        else:
            return False, f"Invalid phone number: {phone}"
