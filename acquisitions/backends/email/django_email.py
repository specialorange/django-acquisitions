"""
Default Django email backend.

Uses Django's built-in email functionality.
"""

import logging
import uuid

from django.core.mail import EmailMultiAlternatives

from ..base import BaseEmailBackend, SendResult
from ...settings import acquisitions_settings

logger = logging.getLogger(__name__)


class DjangoEmailBackend(BaseEmailBackend):
    """Email backend using Django's built-in email system."""

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
        """Send email via Django's email system."""
        try:
            # Normalize to list
            if isinstance(to, str):
                to = [to]

            from_addr = from_email or acquisitions_settings.DEFAULT_FROM_EMAIL
            reply_to_list = [reply_to] if reply_to else None

            # Create message
            msg = EmailMultiAlternatives(
                subject=subject,
                body=body_text,
                from_email=from_addr,
                to=to,
                cc=cc or [],
                bcc=bcc or [],
                reply_to=reply_to_list,
            )

            # Add HTML alternative if provided
            if body_html:
                msg.attach_alternative(body_html, "text/html")

            # Add attachments
            if attachments:
                for attachment in attachments:
                    msg.attach(
                        attachment.get("filename", "attachment"),
                        attachment.get("content", ""),
                        attachment.get("mimetype", "application/octet-stream"),
                    )

            # Send
            msg.send(fail_silently=False)

            # Generate a message ID (Django doesn't return one)
            message_id = str(uuid.uuid4())

            logger.info(f"Email sent to {to}: {subject}")

            return SendResult(
                success=True,
                message_id=message_id,
                metadata={"to": to, "subject": subject},
            )

        except Exception as e:
            logger.exception(f"Failed to send email to {to}")
            return SendResult(success=False, error=str(e))
