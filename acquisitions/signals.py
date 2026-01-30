"""
Django signals for customer acquisition.

These signals allow the consuming project to hook into
acquisition events without modifying the package.
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import Signal, receiver

from .models import Lead, LeadContact

# Custom signals that projects can connect to
lead_converted = Signal()  # Sent when a lead is converted to a customer
lead_status_changed = Signal()  # Sent when lead status changes
new_touchpoint = Signal()  # Sent when a new touchpoint is created


@receiver(pre_save, sender=Lead)
def track_lead_status_change(sender, instance, **kwargs):
    """Track when lead status changes."""
    if instance.pk:
        try:
            old_instance = Lead.objects.get(pk=instance.pk)
            instance._old_status = old_instance.status
        except Lead.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


@receiver(post_save, sender=Lead)
def send_lead_status_changed_signal(sender, instance, created, **kwargs):
    """Send signal when lead status changes."""
    old_status = getattr(instance, "_old_status", None)

    if not created and old_status and old_status != instance.status:
        lead_status_changed.send(
            sender=sender,
            lead=instance,
            old_status=old_status,
            new_status=instance.status,
        )

        # Also send converted signal if applicable
        if instance.status == Lead.Status.WON and old_status != Lead.Status.WON:
            lead_converted.send(
                sender=sender,
                lead=instance,
            )


@receiver(post_save, sender=LeadContact)
def ensure_single_primary_contact(sender, instance, created, **kwargs):
    """
    Ensure only one primary contact per lead.

    This is also handled in LeadContact.save() but this signal
    provides a backup and handles edge cases.
    """
    if instance.is_primary and instance.lead_id:
        # Unset other primary contacts (excluding this one)
        LeadContact.objects.filter(
            lead_id=instance.lead_id,
            is_primary=True,
        ).exclude(pk=instance.pk).update(is_primary=False)
