"""
Celery tasks for follow-up reminders.

These tasks are optional - requires: pip install django-acquisitions[celery]
"""

import logging
from datetime import timedelta

from django.utils import timezone

from ..settings import acquisitions_settings

logger = logging.getLogger(__name__)

# Only define tasks if Celery is available
try:
    from celery import shared_task

    @shared_task(queue=acquisitions_settings.CELERY_QUEUE)
    def send_follow_up_reminders_task(days_without_contact: int = 7) -> dict:
        """
        Send reminders for leads that haven't been contacted recently.

        Args:
            days_without_contact: Number of days without contact to trigger reminder

        Returns:
            dict with reminder stats
        """
        from ..models import Lead, SellerProfile

        cutoff = timezone.now() - timedelta(days=days_without_contact)

        # Find active leads with no recent touchpoints
        stale_leads = Lead.objects.filter(
            status__in=[
                Lead.Status.NEW,
                Lead.Status.CONTACTED,
                Lead.Status.QUALIFIED,
                Lead.Status.PROPOSAL,
                Lead.Status.NEGOTIATION,
            ],
        ).exclude(
            touchpoints__occurred_at__gte=cutoff,
        )

        reminders_sent = 0

        for lead in stale_leads:
            if lead.assigned_to_id:
                # Get seller profile
                try:
                    seller = SellerProfile.objects.get(user_id=lead.assigned_to_id)
                    # Here you would send an email/notification to the seller
                    # This is a placeholder - integrate with your notification system
                    logger.info(
                        f"Reminder needed: Lead {lead.id} ({lead.company_name}) "
                        f"assigned to {seller.display_name}"
                    )
                    reminders_sent += 1
                except SellerProfile.DoesNotExist:
                    pass

        logger.info(f"Generated {reminders_sent} follow-up reminders")
        return {"reminders_sent": reminders_sent}

    @shared_task(queue=acquisitions_settings.CELERY_QUEUE)
    def update_lead_scores_task() -> dict:
        """
        Periodically update lead scores based on engagement.

        This is a placeholder for implementing lead scoring logic.
        """
        from ..models import Lead

        updated = 0

        # Example scoring logic - customize for your needs
        for lead in Lead.objects.filter(status__in=[Lead.Status.NEW, Lead.Status.CONTACTED]):
            score = 0

            # Score based on touchpoints
            touchpoint_count = lead.touchpoints.count()
            score += min(touchpoint_count * 5, 25)  # Max 25 points from touchpoints

            # Score based on contacts
            contact_count = lead.contacts.count()
            score += min(contact_count * 10, 30)  # Max 30 points from contacts

            # Score based on estimated value
            if lead.estimated_value:
                if lead.estimated_value >= 100000:
                    score += 30
                elif lead.estimated_value >= 50000:
                    score += 20
                elif lead.estimated_value >= 10000:
                    score += 10

            # Score based on responses
            has_inbound = lead.touchpoints.filter(direction="inbound").exists()
            if has_inbound:
                score += 15

            if lead.score != score:
                lead.score = score
                lead.save(update_fields=["score", "updated_at"])
                updated += 1

        logger.info(f"Updated scores for {updated} leads")
        return {"updated": updated}

except ImportError:
    # Celery not installed - provide sync versions
    def send_follow_up_reminders_task(days_without_contact: int = 7) -> dict:
        """Sync version when Celery not installed."""
        logger.warning("Celery not installed - running sync version")
        # Implement sync logic here if needed
        return {"reminders_sent": 0}

    def update_lead_scores_task() -> dict:
        """Sync version when Celery not installed."""
        logger.warning("Celery not installed - running sync version")
        return {"updated": 0}
