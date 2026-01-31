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
        Send reminders for prospective clients that haven't been contacted recently.

        Args:
            days_without_contact: Number of days without contact to trigger reminder

        Returns:
            dict with reminder stats
        """
        from ..models import ProspectiveClient, SellerProfile

        cutoff = timezone.now() - timedelta(days=days_without_contact)

        # Find active prospective clients with no recent touchpoints
        stale_prospects = ProspectiveClient.objects.filter(
            status__in=[
                ProspectiveClient.Status.NEW,
                ProspectiveClient.Status.CONTACTED,
                ProspectiveClient.Status.QUALIFIED,
                ProspectiveClient.Status.PROPOSAL,
                ProspectiveClient.Status.NEGOTIATION,
            ],
        ).exclude(
            touchpoints__occurred_at__gte=cutoff,
        )

        reminders_sent = 0

        for prospect in stale_prospects:
            if prospect.assigned_to_id:
                # Get seller profile
                try:
                    seller = SellerProfile.objects.get(user_id=prospect.assigned_to_id)
                    # Here you would send an email/notification to the seller
                    # This is a placeholder - integrate with your notification system
                    logger.info(
                        f"Reminder needed: {prospect.company_name} (ID: {prospect.id}) "
                        f"assigned to {seller.display_name}"
                    )
                    reminders_sent += 1
                except SellerProfile.DoesNotExist:
                    pass

        logger.info(f"Generated {reminders_sent} follow-up reminders")
        return {"reminders_sent": reminders_sent}

    @shared_task(queue=acquisitions_settings.CELERY_QUEUE)
    def update_prospect_scores_task() -> dict:
        """
        Periodically update prospective client scores based on engagement.

        This is a placeholder for implementing scoring logic.
        """
        from ..models import ProspectiveClient

        updated = 0

        # Example scoring logic - customize for your needs
        for prospect in ProspectiveClient.objects.filter(
            status__in=[ProspectiveClient.Status.NEW, ProspectiveClient.Status.CONTACTED]
        ):
            score = 0

            # Score based on touchpoints
            touchpoint_count = prospect.touchpoints.count()
            score += min(touchpoint_count * 5, 25)  # Max 25 points from touchpoints

            # Score based on contacts
            contact_count = prospect.contacts.count()
            score += min(contact_count * 10, 30)  # Max 30 points from contacts

            # Score based on estimated value
            if prospect.estimated_value:
                if prospect.estimated_value >= 100000:
                    score += 30
                elif prospect.estimated_value >= 50000:
                    score += 20
                elif prospect.estimated_value >= 10000:
                    score += 10

            # Score based on responses
            has_inbound = prospect.touchpoints.filter(direction="inbound").exists()
            if has_inbound:
                score += 15

            if prospect.score != score:
                prospect.score = score
                prospect.save(update_fields=["score", "updated_at"])
                updated += 1

        logger.info(f"Updated scores for {updated} prospective clients")
        return {"updated": updated}

    # Keep old name as alias for backwards compatibility
    update_lead_scores_task = update_prospect_scores_task

except ImportError:
    # Celery not installed - provide sync versions
    def send_follow_up_reminders_task(days_without_contact: int = 7) -> dict:
        """Sync version when Celery not installed."""
        logger.warning("Celery not installed - running sync version")
        # Implement sync logic here if needed
        return {"reminders_sent": 0}

    def update_prospect_scores_task() -> dict:
        """Sync version when Celery not installed."""
        logger.warning("Celery not installed - running sync version")
        return {"updated": 0}

    # Keep old name as alias for backwards compatibility
    update_lead_scores_task = update_prospect_scores_task
