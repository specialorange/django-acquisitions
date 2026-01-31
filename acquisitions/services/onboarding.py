"""
Onboarding service for converting prospective clients to customers.

Handles the handoff from prospective client to customer, with support for
custom callbacks to integrate with the consuming project's
customer/account models.
"""

import logging
from importlib import import_module

from django.utils import timezone

from ..settings import acquisitions_settings

logger = logging.getLogger(__name__)


def _load_callback(callback_path: str):
    """Load a callback function from a dotted path."""
    module_path, func_name = callback_path.rsplit(".", 1)
    module = import_module(module_path)
    return getattr(module, func_name)


def convert_prospective_client(prospective_client, user=None) -> dict:
    """
    Convert a prospective client to a customer.

    This marks the prospective client as won and optionally calls a project-specific
    callback to create the customer record.

    Args:
        prospective_client: The ProspectiveClient instance to convert
        user: The user performing the conversion (optional)

    Returns:
        dict with keys:
            - success: bool
            - customer_id: ID of created customer (if callback provided)
            - error: Error message (if failed)
    """
    from ..models import ProspectiveClient

    # Check if already converted
    if prospective_client.status == ProspectiveClient.Status.WON:
        return {
            "success": False,
            "error": "Prospective client is already converted",
        }

    # Get the onboarding callback if configured
    callback_path = acquisitions_settings.ONBOARDING_CALLBACK
    customer_id = None

    if callback_path:
        try:
            callback = _load_callback(callback_path)
            result = callback(prospective_client, user)

            if not result.get("success"):
                return {
                    "success": False,
                    "error": result.get("error", "Callback failed"),
                }

            customer_id = result.get("customer_id")

        except Exception as e:
            logger.exception(f"Error in onboarding callback for prospective client {prospective_client.id}")
            return {
                "success": False,
                "error": f"Callback error: {str(e)}",
            }

    # Mark prospective client as converted
    prospective_client.status = ProspectiveClient.Status.WON
    prospective_client.converted_at = timezone.now()
    if customer_id:
        prospective_client.converted_to_id = customer_id
    prospective_client.save(update_fields=["status", "converted_at", "converted_to_id", "updated_at"])

    logger.info(f"Prospective client {prospective_client.id} ({prospective_client.company_name}) converted to customer {customer_id}")

    return {
        "success": True,
        "customer_id": customer_id,
        "prospective_client_id": prospective_client.id,
    }


def prepare_onboarding_data(prospective_client) -> dict:
    """
    Prepare prospective client data for onboarding/handoff.

    Returns a dictionary with all prospective client data formatted for
    customer creation in the consuming project.

    Args:
        prospective_client: The ProspectiveClient instance

    Returns:
        dict with prospective client data ready for customer creation
    """
    # Get primary contact
    primary_contact = prospective_client.contacts.filter(is_primary=True).first()
    if not primary_contact:
        primary_contact = prospective_client.contacts.first()

    data = {
        "company": {
            "name": prospective_client.company_name,
            "industry": prospective_client.industry.name if prospective_client.industry else None,
            "website": prospective_client.website,
            "address": {
                "line1": prospective_client.address_line1,
                "line2": prospective_client.address_line2,
                "city": prospective_client.city,
                "state": prospective_client.state,
                "postal_code": prospective_client.postal_code,
                "country": prospective_client.country,
            },
        },
        "primary_email": primary_contact.email if primary_contact else None,
        "primary_phone": primary_contact.phone if primary_contact else None,
        "estimated_value": float(prospective_client.estimated_value) if prospective_client.estimated_value else None,
        "source": prospective_client.source,
        "notes": prospective_client.notes,
        "prospective_client_uuid": str(prospective_client.uuid),
    }

    # Add primary contact if exists
    if primary_contact:
        data["primary_contact"] = {
            "first_name": primary_contact.first_name,
            "last_name": primary_contact.last_name,
            "title": primary_contact.title,
            "email": primary_contact.email,
            "phone": primary_contact.phone,
            "phone_mobile": primary_contact.phone_mobile,
        }

    # Add all contacts
    data["contacts"] = [
        {
            "first_name": c.first_name,
            "last_name": c.last_name,
            "title": c.title,
            "role": c.role,
            "email": c.email,
            "phone": c.phone,
            "phone_mobile": c.phone_mobile,
            "is_primary": c.is_primary,
            "preferred_contact_method": c.preferred_contact_method,
        }
        for c in prospective_client.contacts.all()
    ]

    return data
