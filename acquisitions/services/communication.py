"""
Communication service for email and SMS.

Provides a unified interface for sending communications,
with backend abstraction for different providers.
"""

import logging
from importlib import import_module

from django.template import Context, Template

from ..backends.base import BaseEmailBackend, BaseSMSBackend, SendResult
from ..settings import acquisitions_settings

logger = logging.getLogger(__name__)

# Cache for backend instances
_email_backend_instance = None
_sms_backend_instance = None


def _load_backend(backend_path: str):
    """Load a backend class from a dotted path."""
    module_path, class_name = backend_path.rsplit(".", 1)
    module = import_module(module_path)
    return getattr(module, class_name)


def get_email_backend() -> BaseEmailBackend:
    """Get the configured email backend instance."""
    global _email_backend_instance
    if _email_backend_instance is None:
        backend_class = _load_backend(acquisitions_settings.EMAIL_BACKEND)
        _email_backend_instance = backend_class()
    return _email_backend_instance


def get_sms_backend() -> BaseSMSBackend:
    """Get the configured SMS backend instance."""
    global _sms_backend_instance
    if _sms_backend_instance is None:
        backend_class = _load_backend(acquisitions_settings.SMS_BACKEND)
        _sms_backend_instance = backend_class()
    return _sms_backend_instance


def render_template(template_string: str, context: dict) -> str:
    """Render a Django template string with context."""
    template = Template(template_string)
    return template.render(Context(context))


def send_email(
    to: str | list[str],
    subject: str,
    body_text: str,
    body_html: str | None = None,
    context: dict | None = None,
    from_email: str | None = None,
    reply_to: str | None = None,
    **kwargs,
) -> SendResult:
    """
    Send an email, optionally rendering templates with context.

    Args:
        to: Recipient email(s)
        subject: Email subject (can be a template)
        body_text: Plain text body (can be a template)
        body_html: Optional HTML body (can be a template)
        context: Template context for rendering
        from_email: Sender email
        reply_to: Reply-to address
        **kwargs: Additional arguments passed to backend

    Returns:
        SendResult
    """
    # Render templates if context provided
    if context:
        subject = render_template(subject, context)
        body_text = render_template(body_text, context)
        if body_html:
            body_html = render_template(body_html, context)

    backend = get_email_backend()
    return backend.send_email(
        to=to,
        subject=subject,
        body_text=body_text,
        body_html=body_html,
        from_email=from_email,
        reply_to=reply_to,
        **kwargs,
    )


def send_sms(
    to: str,
    body: str,
    context: dict | None = None,
    from_number: str | None = None,
) -> SendResult:
    """
    Send an SMS, optionally rendering template with context.

    Args:
        to: Recipient phone number
        body: Message body (can be a template)
        context: Template context for rendering
        from_number: Sender phone number

    Returns:
        SendResult
    """
    # Render template if context provided
    if context:
        body = render_template(body, context)

    backend = get_sms_backend()
    return backend.send_sms(to=to, body=body, from_number=from_number)
