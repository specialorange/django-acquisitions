"""
Django signals for customer acquisition.

These signals allow the consuming project to hook into
acquisition events without modifying the package.
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import Signal, receiver

from .models import ProspectiveClient, ProspectiveClientContact

# Custom signals that projects can connect to
prospective_client_converted = Signal()  # Sent when a prospective client is converted to a customer
prospective_client_status_changed = Signal()  # Sent when prospective client status changes
new_touchpoint = Signal()  # Sent when a new touchpoint is created

@receiver(pre_save, sender=ProspectiveClient)
def track_prospective_client_status_change(sender, instance, **kwargs):
    """Track when prospective client status changes."""
    if instance.pk:
        try:
            old_instance = ProspectiveClient.objects.get(pk=instance.pk)
            instance._old_status = old_instance.status
        except ProspectiveClient.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


@receiver(post_save, sender=ProspectiveClient)
def send_prospective_client_status_changed_signal(sender, instance, created, **kwargs):
    """Send signal when prospective client status changes."""
    old_status = getattr(instance, "_old_status", None)

    if not created and old_status and old_status != instance.status:
        prospective_client_status_changed.send(
            sender=sender,
            prospective_client=instance,
            old_status=old_status,
            new_status=instance.status,
        )

        # Also send converted signal if applicable
        if instance.status == ProspectiveClient.Status.WON and old_status != ProspectiveClient.Status.WON:
            prospective_client_converted.send(
                sender=sender,
                prospective_client=instance,
            )


@receiver(post_save, sender=ProspectiveClientContact)
def ensure_single_primary_contact(sender, instance, created, **kwargs):
    """
    Ensure only one primary contact per prospective client.

    This is also handled in ProspectiveClientContact.save() but this signal
    provides a backup and handles edge cases.
    """
    if instance.is_primary and instance.prospective_client_id:
        # Unset other primary contacts (excluding this one)
        ProspectiveClientContact.objects.filter(
            prospective_client_id=instance.prospective_client_id,
            is_primary=True,
        ).exclude(pk=instance.pk).update(is_primary=False)
