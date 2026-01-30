"""
Service tests for django-acquisitions.
"""

import pytest
from django.utils import timezone

from acquisitions.models import CampaignEnrollment, CampaignStep, Lead, Touchpoint
from acquisitions.services.communication import render_template, send_email, send_sms
from acquisitions.services.onboarding import convert_lead, prepare_onboarding_data
from acquisitions.services.outreach import (
    enroll_lead_in_campaign,
    execute_campaign_step,
    process_scheduled_outreach,
)


@pytest.mark.django_db
class TestCommunicationService:
    """Tests for communication service."""

    def test_render_template(self):
        """Test template rendering."""
        template = "Hello {{ name }}, welcome to {{ company }}!"
        result = render_template(template, {"name": "John", "company": "Acme"})
        assert result == "Hello John, welcome to Acme!"

    def test_send_email(self, lead):
        """Test sending email."""
        result = send_email(
            to=lead.email,
            subject="Test Subject",
            body_text="Test body",
        )
        # Should succeed with locmem backend
        assert result.success is True

    def test_send_email_with_template(self, lead):
        """Test sending email with template."""
        result = send_email(
            to=lead.email,
            subject="Hello {{ company_name }}",
            body_text="Welcome to our service, {{ company_name }}!",
            context={"company_name": lead.company_name},
        )
        assert result.success is True

    def test_send_sms(self, lead):
        """Test sending SMS (console backend)."""
        lead.phone = "5551234567"
        lead.save()

        result = send_sms(
            to=lead.phone,
            body="Test SMS message",
        )
        # Console backend always succeeds
        assert result.success is True


@pytest.mark.django_db
class TestOnboardingService:
    """Tests for onboarding service."""

    def test_convert_lead(self, lead, user):
        """Test lead conversion."""
        result = convert_lead(lead, user)

        assert result["success"] is True
        assert result["lead_id"] == lead.id

        lead.refresh_from_db()
        assert lead.status == Lead.Status.WON
        assert lead.converted_at is not None

    def test_convert_already_converted(self, lead_factory, user):
        """Test converting already converted lead."""
        lead = lead_factory(status=Lead.Status.WON)

        result = convert_lead(lead, user)
        assert result["success"] is False
        assert "already converted" in result["error"].lower()

    def test_prepare_onboarding_data(self, lead, contact_factory):
        """Test preparing onboarding data."""
        contact = contact_factory(lead, is_primary=True)

        data = prepare_onboarding_data(lead)

        assert data["company"]["name"] == lead.company_name
        assert data["primary_email"] == lead.email
        assert data["primary_contact"]["first_name"] == contact.first_name
        assert len(data["contacts"]) == 1


@pytest.mark.django_db
class TestOutreachService:
    """Tests for outreach service."""

    def test_enroll_lead_in_campaign(self, lead, campaign, campaign_step_factory):
        """Test enrolling a lead in a campaign."""
        campaign_step_factory(campaign, step_order=0)

        enrollment = enroll_lead_in_campaign(lead, campaign)

        assert enrollment.lead == lead
        assert enrollment.campaign == campaign
        assert enrollment.is_active is True
        assert enrollment.next_step_scheduled_at is not None

    def test_enroll_already_enrolled(self, lead, campaign):
        """Test enrolling already enrolled lead."""
        CampaignEnrollment.objects.create(lead=lead, campaign=campaign, is_active=True)

        with pytest.raises(ValueError):
            enroll_lead_in_campaign(lead, campaign)

    def test_execute_campaign_step_email(
        self, lead, campaign, campaign_step_factory, contact_factory
    ):
        """Test executing an email campaign step."""
        contact_factory(lead, is_primary=True)
        step = campaign_step_factory(campaign, step_order=0, step_type=CampaignStep.StepType.EMAIL)

        enrollment = CampaignEnrollment.objects.create(
            lead=lead,
            campaign=campaign,
            current_step=0,
        )

        result = execute_campaign_step(enrollment)

        assert result["success"] is True

        # Check touchpoint was created
        assert Touchpoint.objects.filter(
            lead=lead,
            touchpoint_type=Touchpoint.TouchpointType.EMAIL,
            is_automated=True,
        ).exists()

    def test_execute_campaign_step_skip_responded(
        self, lead, campaign, campaign_step_factory, touchpoint_factory
    ):
        """Test skipping step when lead has responded."""
        step = campaign_step_factory(
            campaign, step_order=0, step_type=CampaignStep.StepType.EMAIL, skip_if_responded=True
        )

        enrollment = CampaignEnrollment.objects.create(
            lead=lead,
            campaign=campaign,
            current_step=0,
        )

        # Create inbound touchpoint after enrollment
        touchpoint_factory(
            lead,
            direction=Touchpoint.Direction.INBOUND,
            occurred_at=timezone.now(),
        )

        result = execute_campaign_step(enrollment)

        assert result["success"] is True
        assert result.get("skipped") is True
        assert result.get("reason") == "lead_responded"

    def test_process_scheduled_outreach(
        self, lead, campaign, campaign_step_factory, contact_factory
    ):
        """Test processing scheduled outreach."""
        contact_factory(lead, is_primary=True)
        campaign_step_factory(campaign, step_order=0)

        # Create enrollment due for processing
        enrollment = CampaignEnrollment.objects.create(
            lead=lead,
            campaign=campaign,
            current_step=0,
            next_step_scheduled_at=timezone.now() - timezone.timedelta(hours=1),
        )

        result = process_scheduled_outreach()

        assert result["processed"] >= 1
