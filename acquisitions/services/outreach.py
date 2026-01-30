"""
Outreach service for managing campaign execution.

Handles campaign enrollment, step execution, and scheduling.
"""

import logging
from datetime import timedelta

from django.utils import timezone

from ..models import CampaignEnrollment, CampaignStep, Lead, OutreachCampaign, Touchpoint
from ..settings import acquisitions_settings
from .communication import send_email, send_sms

logger = logging.getLogger(__name__)


def enroll_lead_in_campaign(lead: Lead, campaign: OutreachCampaign) -> CampaignEnrollment:
    """
    Enroll a lead in an outreach campaign.

    Args:
        lead: The lead to enroll
        campaign: The campaign to enroll in

    Returns:
        CampaignEnrollment instance

    Raises:
        ValueError if lead is already actively enrolled
    """
    # Check for existing active enrollment
    existing = CampaignEnrollment.objects.filter(
        lead=lead,
        campaign=campaign,
        is_active=True,
    ).first()

    if existing:
        raise ValueError(f"Lead {lead.id} is already enrolled in campaign {campaign.id}")

    # Create enrollment
    enrollment = CampaignEnrollment.objects.create(
        lead=lead,
        campaign=campaign,
        current_step=0,
        is_active=True,
    )

    # Schedule first step
    first_step = campaign.steps.filter(is_active=True).order_by("step_order").first()
    if first_step:
        delay = timedelta(days=first_step.delay_days, hours=first_step.delay_hours)
        enrollment.next_step_scheduled_at = timezone.now() + delay
        enrollment.save(update_fields=["next_step_scheduled_at"])

    logger.info(f"Lead {lead.id} enrolled in campaign {campaign.id}")
    return enrollment


def execute_campaign_step(enrollment: CampaignEnrollment) -> dict:
    """
    Execute the current campaign step for an enrollment.

    Args:
        enrollment: The CampaignEnrollment to process

    Returns:
        dict with execution result
    """
    if not enrollment.is_active:
        return {"success": False, "error": "Enrollment not active"}

    # Get current step
    try:
        step = enrollment.campaign.steps.get(
            step_order=enrollment.current_step,
            is_active=True,
        )
    except CampaignStep.DoesNotExist:
        # No more steps - complete the campaign
        enrollment.is_active = False
        enrollment.completed_at = timezone.now()
        enrollment.save()
        return {"success": True, "completed": True}

    lead = enrollment.lead

    # Check skip conditions
    if step.skip_if_responded:
        has_inbound = lead.touchpoints.filter(
            direction="inbound",
            occurred_at__gt=enrollment.enrolled_at,
        ).exists()
        if has_inbound:
            logger.info(f"Skipping step for lead {lead.id} - has responded")
            _advance_enrollment(enrollment)
            return {"success": True, "skipped": True, "reason": "lead_responded"}

    # Execute based on step type
    result = {"success": False}

    if step.step_type == CampaignStep.StepType.EMAIL:
        result = _execute_email_step(enrollment, step)
    elif step.step_type == CampaignStep.StepType.SMS:
        result = _execute_sms_step(enrollment, step)
    elif step.step_type == CampaignStep.StepType.TASK:
        result = _execute_task_step(enrollment, step)
    elif step.step_type == CampaignStep.StepType.WAIT:
        result = {"success": True}

    if result.get("success"):
        _advance_enrollment(enrollment)

    return result


def _advance_enrollment(enrollment: CampaignEnrollment):
    """Advance enrollment to the next step."""
    next_step_num = enrollment.current_step + 1

    try:
        next_step = enrollment.campaign.steps.get(
            step_order=next_step_num,
            is_active=True,
        )

        # Calculate next execution time
        delay = timedelta(days=next_step.delay_days, hours=next_step.delay_hours)
        enrollment.current_step = next_step_num
        enrollment.next_step_scheduled_at = timezone.now() + delay
        enrollment.save()

    except CampaignStep.DoesNotExist:
        # No more steps - complete
        enrollment.is_active = False
        enrollment.completed_at = timezone.now()
        enrollment.save()


def _execute_email_step(enrollment: CampaignEnrollment, step: CampaignStep) -> dict:
    """Execute an email campaign step."""
    lead = enrollment.lead

    # Get primary contact or use lead email
    contact = lead.contacts.filter(is_primary=True).first()
    to_email = contact.email if contact and contact.email else lead.email

    if not to_email:
        return {"success": False, "error": "No email address"}

    # Check opt-out
    if contact and contact.opted_out_email:
        return {"success": False, "error": "Contact opted out of email", "skipped": True}

    # Build context for template rendering
    context = {
        "lead": lead,
        "contact": contact,
        "company_name": lead.company_name,
        "first_name": contact.first_name if contact else "",
        "last_name": contact.last_name if contact else "",
    }

    result = send_email(
        to=to_email,
        subject=step.subject_template,
        body_text=step.body_template,
        context=context,
    )

    if result.success:
        # Create touchpoint record
        Touchpoint.objects.create(
            lead=lead,
            touchpoint_type=Touchpoint.TouchpointType.EMAIL,
            direction=Touchpoint.Direction.OUTBOUND,
            contact=contact,
            subject=step.subject_template,
            notes=f"Campaign: {enrollment.campaign.name}",
            occurred_at=timezone.now(),
            is_automated=True,
            campaign=enrollment.campaign,
            external_id=result.message_id or "",
        )

    return {"success": result.success, "error": result.error}


def _execute_sms_step(enrollment: CampaignEnrollment, step: CampaignStep) -> dict:
    """Execute an SMS campaign step."""
    lead = enrollment.lead

    # Get primary contact or use lead phone
    contact = lead.contacts.filter(is_primary=True).first()
    to_phone = None

    if contact:
        to_phone = contact.phone_mobile or contact.phone
    if not to_phone:
        to_phone = lead.phone

    if not to_phone:
        return {"success": False, "error": "No phone number"}

    # Check opt-out
    if contact and contact.opted_out_sms:
        return {"success": False, "error": "Contact opted out of SMS", "skipped": True}

    # Build context
    context = {
        "lead": lead,
        "contact": contact,
        "company_name": lead.company_name,
        "first_name": contact.first_name if contact else "",
    }

    result = send_sms(
        to=to_phone,
        body=step.body_template,
        context=context,
    )

    if result.success:
        # Create touchpoint record
        Touchpoint.objects.create(
            lead=lead,
            touchpoint_type=Touchpoint.TouchpointType.SMS,
            direction=Touchpoint.Direction.OUTBOUND,
            contact=contact,
            notes=f"Campaign: {enrollment.campaign.name}\n{step.body_template[:100]}",
            occurred_at=timezone.now(),
            is_automated=True,
            campaign=enrollment.campaign,
            external_id=result.message_id or "",
        )

    return {"success": result.success, "error": result.error}


def _execute_task_step(enrollment: CampaignEnrollment, step: CampaignStep) -> dict:
    """
    Execute a manual task step.

    Creates a touchpoint as a reminder that manual action is needed.
    """
    lead = enrollment.lead

    # Create a touchpoint as a task reminder
    Touchpoint.objects.create(
        lead=lead,
        touchpoint_type=Touchpoint.TouchpointType.OTHER,
        direction=Touchpoint.Direction.OUTBOUND,
        subject=f"Task: {step.subject_template}" if step.subject_template else "Manual Task",
        notes=f"Campaign: {enrollment.campaign.name}\n\n{step.body_template}",
        occurred_at=timezone.now(),
        outcome=Touchpoint.Outcome.FOLLOW_UP,
        is_automated=True,
        campaign=enrollment.campaign,
    )

    return {"success": True, "task_created": True}


def get_due_enrollments():
    """Get all enrollments that are due for processing."""
    now = timezone.now()
    return CampaignEnrollment.objects.filter(
        is_active=True,
        next_step_scheduled_at__lte=now,
    ).select_related("lead", "campaign")


def process_scheduled_outreach() -> dict:
    """
    Process all due campaign steps.

    This should be called periodically (e.g., via Celery beat or cron).

    Returns:
        dict with processing stats
    """
    due_enrollments = get_due_enrollments()

    processed = 0
    succeeded = 0
    failed = 0

    for enrollment in due_enrollments:
        try:
            result = execute_campaign_step(enrollment)
            processed += 1
            if result.get("success"):
                succeeded += 1
            else:
                failed += 1
        except Exception as e:
            logger.exception(f"Error processing enrollment {enrollment.id}")
            failed += 1

    logger.info(f"Processed {processed} enrollments: {succeeded} succeeded, {failed} failed")

    return {
        "processed": processed,
        "succeeded": succeeded,
        "failed": failed,
    }
