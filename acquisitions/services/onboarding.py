"""
Onboarding service for converting leads to customers.

Handles the handoff from lead to customer, with support for
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


def convert_lead(lead, user=None) -> dict:
    """
    Convert a lead to a customer.

    This marks the lead as won and optionally calls a project-specific
    callback to create the customer record.

    Args:
        lead: The Lead instance to convert
        user: The user performing the conversion (optional)

    Returns:
        dict with keys:
            - success: bool
            - customer_id: ID of created customer (if callback provided)
            - error: Error message (if failed)
    """
    from ..models import Lead

    # Check if already converted
    if lead.status == Lead.Status.WON:
        return {
            "success": False,
            "error": "Lead is already converted",
        }

    # Get the onboarding callback if configured
    callback_path = acquisitions_settings.ONBOARDING_CALLBACK
    customer_id = None

    if callback_path:
        try:
            callback = _load_callback(callback_path)
            result = callback(lead, user)

            if not result.get("success"):
                return {
                    "success": False,
                    "error": result.get("error", "Callback failed"),
                }

            customer_id = result.get("customer_id")

        except Exception as e:
            logger.exception(f"Error in onboarding callback for lead {lead.id}")
            return {
                "success": False,
                "error": f"Callback error: {str(e)}",
            }

    # Mark lead as converted
    lead.status = Lead.Status.WON
    lead.converted_at = timezone.now()
    if customer_id:
        lead.converted_to_id = customer_id
    lead.save(update_fields=["status", "converted_at", "converted_to_id", "updated_at"])

    logger.info(f"Lead {lead.id} ({lead.company_name}) converted to customer {customer_id}")

    return {
        "success": True,
        "customer_id": customer_id,
        "lead_id": lead.id,
    }


def prepare_onboarding_data(lead) -> dict:
    """
    Prepare lead data for onboarding/handoff.

    Returns a dictionary with all lead data formatted for
    customer creation in the consuming project.

    Args:
        lead: The Lead instance

    Returns:
        dict with lead data ready for customer creation
    """
    # Get primary contact
    primary_contact = lead.contacts.filter(is_primary=True).first()
    if not primary_contact:
        primary_contact = lead.contacts.first()

    data = {
        "company": {
            "name": lead.company_name,
            "industry": lead.industry,
            "website": lead.website,
            "address": {
                "line1": lead.address_line1,
                "line2": lead.address_line2,
                "city": lead.city,
                "state": lead.state,
                "postal_code": lead.postal_code,
                "country": lead.country,
            },
        },
        "primary_email": lead.email,
        "primary_phone": lead.phone,
        "estimated_value": float(lead.estimated_value) if lead.estimated_value else None,
        "source": lead.source,
        "notes": lead.notes,
        "lead_uuid": str(lead.uuid),
    }

    # Add primary contact if exists
    if primary_contact:
        data["primary_contact"] = {
            "first_name": primary_contact.first_name,
            "last_name": primary_contact.last_name,
            "title": primary_contact.title,
            "email": primary_contact.email or lead.email,
            "phone": primary_contact.phone or lead.phone,
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
        for c in lead.contacts.all()
    ]

    return data
