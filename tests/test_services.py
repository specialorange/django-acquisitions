"""
Service tests for django-acquisitions.
"""

import pytest
from django.utils import timezone

from acquisitions.models import CampaignEnrollment, CampaignStep, ProspectiveClient, Touchpoint
from acquisitions.services.communication import render_template, send_email, send_sms
from acquisitions.services.onboarding import convert_prospective_client, prepare_onboarding_data
from acquisitions.services.outreach import (
    enroll_prospective_client_in_campaign,
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

    def test_send_email(self, prospective_client, contact_factory):
        """Test sending email."""
        contact = contact_factory(prospective_client, email="test@example.com")
        result = send_email(
            to=contact.email,
            subject="Test Subject",
            body_text="Test body",
        )
        # Should succeed with locmem backend
        assert result.success is True

    def test_send_email_with_template(self, prospective_client, contact_factory):
        """Test sending email with template."""
        contact = contact_factory(prospective_client, email="test@example.com")
        result = send_email(
            to=contact.email,
            subject="Hello {{ company_name }}",
            body_text="Welcome to our service, {{ company_name }}!",
            context={"company_name": prospective_client.company_name},
        )
        assert result.success is True

    def test_send_sms(self, prospective_client, contact_factory):
        """Test sending SMS (console backend)."""
        contact = contact_factory(prospective_client, phone="5551234567")

        result = send_sms(
            to=contact.phone,
            body="Test SMS message",
        )
        # Console backend always succeeds
        assert result.success is True


@pytest.mark.django_db
class TestOnboardingService:
    """Tests for onboarding service."""

    def test_convert_prospective_client(self, prospective_client, user):
        """Test prospective client conversion."""
        result = convert_prospective_client(prospective_client, user)

        assert result["success"] is True
        assert result["prospective_client_id"] == prospective_client.id

        prospective_client.refresh_from_db()
        assert prospective_client.status == ProspectiveClient.Status.WON
        assert prospective_client.converted_at is not None

    def test_convert_already_converted(self, prospective_client_factory, user):
        """Test converting already converted prospective client."""
        pc = prospective_client_factory(status=ProspectiveClient.Status.WON)

        result = convert_prospective_client(pc, user)
        assert result["success"] is False
        assert "already converted" in result["error"].lower()

    def test_prepare_onboarding_data(self, prospective_client, contact_factory):
        """Test preparing onboarding data."""
        contact = contact_factory(prospective_client, is_primary=True, email="primary@example.com")

        data = prepare_onboarding_data(prospective_client)

        assert data["company"]["name"] == prospective_client.company_name
        assert data["primary_email"] == contact.email
        assert data["primary_contact"]["first_name"] == contact.first_name
        assert len(data["contacts"]) == 1


@pytest.mark.django_db
class TestOutreachService:
    """Tests for outreach service."""

    def test_enroll_prospective_client_in_campaign(self, prospective_client, campaign, campaign_step_factory):
        """Test enrolling a prospective client in a campaign."""
        campaign_step_factory(campaign, step_order=0)

        enrollment = enroll_prospective_client_in_campaign(prospective_client, campaign)

        assert enrollment.prospective_client == prospective_client
        assert enrollment.campaign == campaign
        assert enrollment.is_active is True
        assert enrollment.next_step_scheduled_at is not None

    def test_enroll_already_enrolled(self, prospective_client, campaign):
        """Test enrolling already enrolled prospective client."""
        CampaignEnrollment.objects.create(
            prospective_client=prospective_client, campaign=campaign, is_active=True
        )

        with pytest.raises(ValueError):
            enroll_prospective_client_in_campaign(prospective_client, campaign)

    def test_execute_campaign_step_email(
        self, prospective_client, campaign, campaign_step_factory, contact_factory
    ):
        """Test executing an email campaign step."""
        contact_factory(prospective_client, is_primary=True)
        step = campaign_step_factory(campaign, step_order=0, step_type=CampaignStep.StepType.EMAIL)

        enrollment = CampaignEnrollment.objects.create(
            prospective_client=prospective_client,
            campaign=campaign,
            current_step=0,
        )

        result = execute_campaign_step(enrollment)

        assert result["success"] is True

        # Check touchpoint was created
        assert Touchpoint.objects.filter(
            prospective_client=prospective_client,
            touchpoint_type=Touchpoint.TouchpointType.EMAIL,
            is_automated=True,
        ).exists()

    def test_execute_campaign_step_skip_responded(
        self, prospective_client, campaign, campaign_step_factory, touchpoint_factory
    ):
        """Test skipping step when prospective client has responded."""
        step = campaign_step_factory(
            campaign, step_order=0, step_type=CampaignStep.StepType.EMAIL, skip_if_responded=True
        )

        enrollment = CampaignEnrollment.objects.create(
            prospective_client=prospective_client,
            campaign=campaign,
            current_step=0,
        )

        # Create inbound touchpoint after enrollment
        touchpoint_factory(
            prospective_client,
            direction=Touchpoint.Direction.INBOUND,
            occurred_at=timezone.now(),
        )

        result = execute_campaign_step(enrollment)

        assert result["success"] is True
        assert result.get("skipped") is True
        assert result.get("reason") == "prospective_client_responded"

    def test_process_scheduled_outreach(
        self, prospective_client, campaign, campaign_step_factory, contact_factory
    ):
        """Test processing scheduled outreach."""
        contact_factory(prospective_client, is_primary=True)
        campaign_step_factory(campaign, step_order=0)

        # Create enrollment due for processing
        enrollment = CampaignEnrollment.objects.create(
            prospective_client=prospective_client,
            campaign=campaign,
            current_step=0,
            next_step_scheduled_at=timezone.now() - timezone.timedelta(hours=1),
        )

        result = process_scheduled_outreach()

        assert result["processed"] >= 1
