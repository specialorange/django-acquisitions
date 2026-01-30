"""
Celery tasks for automated outreach.

These tasks are optional - requires: pip install django-acquisitions[celery]
"""

import logging

from ..settings import acquisitions_settings

logger = logging.getLogger(__name__)

# Only define tasks if Celery is available
try:
    from celery import shared_task

    @shared_task(
        bind=True,
        autoretry_for=(Exception,),
        retry_backoff=True,
        retry_backoff_max=600,
        max_retries=3,
        queue=acquisitions_settings.CELERY_QUEUE,
    )
    def send_campaign_step_task(self, enrollment_id: int) -> dict:
        """
        Execute a campaign step for an enrolled lead.

        Args:
            enrollment_id: CampaignEnrollment ID

        Returns:
            dict with execution result
        """
        from ..models import CampaignEnrollment
        from ..services.outreach import execute_campaign_step

        try:
            enrollment = CampaignEnrollment.objects.select_related("lead", "campaign").get(
                id=enrollment_id
            )
        except CampaignEnrollment.DoesNotExist:
            logger.error(f"Enrollment {enrollment_id} not found")
            return {"success": False, "error": "Enrollment not found"}

        result = execute_campaign_step(enrollment)

        # Schedule next step if needed
        if result.get("success") and enrollment.is_active and enrollment.next_step_scheduled_at:
            if acquisitions_settings.USE_CELERY:
                send_campaign_step_task.apply_async(
                    args=[enrollment.id],
                    eta=enrollment.next_step_scheduled_at,
                )

        return result

    @shared_task(queue=acquisitions_settings.CELERY_QUEUE)
    def process_scheduled_outreach_task() -> dict:
        """
        Periodic task to process scheduled campaign steps.

        Should be called by Celery Beat every 5-15 minutes.
        """
        from ..services.outreach import get_due_enrollments

        due_enrollments = list(get_due_enrollments().values_list("id", flat=True))

        for enrollment_id in due_enrollments:
            if acquisitions_settings.USE_CELERY:
                send_campaign_step_task.delay(enrollment_id)
            else:
                # Fallback to sync execution
                send_campaign_step_task(enrollment_id)

        logger.info(f"Queued {len(due_enrollments)} campaign steps for execution")
        return {"queued": len(due_enrollments)}

except ImportError:
    # Celery not installed - provide sync versions
    def send_campaign_step_task(enrollment_id: int) -> dict:
        """Sync version when Celery not installed."""
        from ..models import CampaignEnrollment
        from ..services.outreach import execute_campaign_step

        try:
            enrollment = CampaignEnrollment.objects.select_related("lead", "campaign").get(
                id=enrollment_id
            )
        except CampaignEnrollment.DoesNotExist:
            return {"success": False, "error": "Enrollment not found"}

        return execute_campaign_step(enrollment)

    def process_scheduled_outreach_task() -> dict:
        """Sync version when Celery not installed."""
        from ..services.outreach import process_scheduled_outreach

        return process_scheduled_outreach()
