"""
Model tests for django-acquisitions.
"""

import pytest
from django.utils import timezone

from acquisitions.models import (
    CampaignEnrollment,
    Lead,
    LeadContact,
    MarketingDocument,
    OutreachCampaign,
    SellerProfile,
    Touchpoint,
)


@pytest.mark.django_db
class TestLead:
    """Tests for Lead model."""

    def test_create_lead(self, lead_factory):
        """Test basic lead creation."""
        lead = lead_factory(company_name="Acme Corp")
        assert lead.company_name == "Acme Corp"
        assert lead.status == Lead.Status.NEW
        assert lead.uuid is not None

    def test_lead_is_active(self, lead_factory):
        """Test is_active property."""
        active_lead = lead_factory(status=Lead.Status.CONTACTED)
        assert active_lead.is_active is True

        won_lead = lead_factory(status=Lead.Status.WON)
        assert won_lead.is_active is False

        lost_lead = lead_factory(status=Lead.Status.LOST)
        assert lost_lead.is_active is False

    def test_lead_is_converted(self, lead_factory):
        """Test is_converted property."""
        lead = lead_factory()
        assert lead.is_converted is False

        lead.status = Lead.Status.WON
        lead.converted_at = timezone.now()
        lead.converted_to_id = 123
        lead.save()

        assert lead.is_converted is True

    def test_mark_converted(self, lead_factory):
        """Test mark_converted method."""
        lead = lead_factory()
        lead.mark_converted(customer_id=456)

        assert lead.status == Lead.Status.WON
        assert lead.converted_at is not None
        assert lead.converted_to_id == 456

    def test_lead_ordering(self, lead_factory):
        """Test lead ordering by priority and score."""
        lead1 = lead_factory(company_name="Low Priority", priority=10, score=50)
        lead2 = lead_factory(company_name="High Priority", priority=1, score=50)
        lead3 = lead_factory(company_name="High Score", priority=1, score=100)

        leads = list(Lead.objects.all())
        assert leads[0] == lead3  # Same priority, higher score
        assert leads[1] == lead2  # Same priority, lower score
        assert leads[2] == lead1  # Lower priority


@pytest.mark.django_db
class TestLeadContact:
    """Tests for LeadContact model."""

    def test_create_contact(self, lead, contact_factory):
        """Test contact creation."""
        contact = contact_factory(lead, first_name="Jane", last_name="Smith")
        assert contact.full_name == "Jane Smith"
        assert contact.lead == lead

    def test_primary_contact(self, lead, contact_factory):
        """Test primary contact handling."""
        contact1 = contact_factory(lead, first_name="John", is_primary=True)
        assert contact1.is_primary is True

        contact2 = contact_factory(lead, first_name="Jane", is_primary=True)
        assert contact2.is_primary is True

        # First contact should no longer be primary
        contact1.refresh_from_db()
        assert contact1.is_primary is False

    def test_contact_ordering(self, lead, contact_factory):
        """Test contact ordering (primary first, then by name)."""
        contact1 = contact_factory(lead, first_name="Zack", last_name="Adams", is_primary=False)
        contact2 = contact_factory(lead, first_name="Alice", last_name="Brown", is_primary=True)
        contact3 = contact_factory(lead, first_name="Bob", last_name="Cooper", is_primary=False)

        contacts = list(lead.contacts.all())
        assert contacts[0] == contact2  # Primary first
        assert contacts[1] == contact3  # Then alphabetically
        assert contacts[2] == contact1


@pytest.mark.django_db
class TestTouchpoint:
    """Tests for Touchpoint model."""

    def test_create_touchpoint(self, lead, touchpoint_factory):
        """Test touchpoint creation."""
        touchpoint = touchpoint_factory(
            lead,
            touchpoint_type=Touchpoint.TouchpointType.EMAIL,
            subject="Introduction",
        )
        assert touchpoint.lead == lead
        assert touchpoint.touchpoint_type == "email"
        assert touchpoint.subject == "Introduction"

    def test_touchpoint_ordering(self, lead, touchpoint_factory):
        """Test touchpoints ordered by occurred_at descending."""
        now = timezone.now()
        tp1 = touchpoint_factory(lead, occurred_at=now - timezone.timedelta(days=2))
        tp2 = touchpoint_factory(lead, occurred_at=now)
        tp3 = touchpoint_factory(lead, occurred_at=now - timezone.timedelta(days=1))

        touchpoints = list(lead.touchpoints.all())
        assert touchpoints[0] == tp2  # Most recent first
        assert touchpoints[1] == tp3
        assert touchpoints[2] == tp1


@pytest.mark.django_db
class TestOutreachCampaign:
    """Tests for OutreachCampaign model."""

    def test_create_campaign(self, campaign_factory):
        """Test campaign creation."""
        campaign = campaign_factory(name="Welcome Series")
        assert campaign.name == "Welcome Series"
        assert campaign.status == OutreachCampaign.Status.ACTIVE
        assert campaign.uuid is not None

    def test_campaign_with_steps(self, campaign_factory, campaign_step_factory):
        """Test campaign with steps."""
        campaign = campaign_factory()
        step1 = campaign_step_factory(campaign, step_order=0)
        step2 = campaign_step_factory(campaign, step_order=1, delay_days=3)
        step3 = campaign_step_factory(campaign, step_order=2, delay_days=7)

        assert campaign.steps.count() == 3
        steps = list(campaign.steps.all())
        assert steps[0] == step1
        assert steps[1] == step2
        assert steps[2] == step3


@pytest.mark.django_db
class TestCampaignEnrollment:
    """Tests for CampaignEnrollment model."""

    def test_enroll_lead(self, lead, campaign):
        """Test enrolling a lead in a campaign."""
        enrollment = CampaignEnrollment.objects.create(
            lead=lead,
            campaign=campaign,
        )
        assert enrollment.is_active is True
        assert enrollment.current_step == 0

    def test_unique_enrollment(self, lead, campaign):
        """Test that a lead can only be enrolled once in a campaign."""
        CampaignEnrollment.objects.create(lead=lead, campaign=campaign)

        with pytest.raises(Exception):  # IntegrityError
            CampaignEnrollment.objects.create(lead=lead, campaign=campaign)


@pytest.mark.django_db
class TestMarketingDocument:
    """Tests for MarketingDocument model."""

    def test_create_document(self):
        """Test document creation."""
        doc = MarketingDocument.objects.create(
            name="Company Brochure",
            document_type=MarketingDocument.DocumentType.BROCHURE,
            version="2.0",
        )
        assert doc.name == "Company Brochure"
        assert doc.version == "2.0"
        assert doc.view_count == 0

    def test_increment_counts(self):
        """Test view and download count incrementing."""
        doc = MarketingDocument.objects.create(
            name="Test Doc",
            document_type=MarketingDocument.DocumentType.OTHER,
        )

        doc.increment_view_count()
        doc.increment_view_count()
        doc.refresh_from_db()
        assert doc.view_count == 2

        doc.increment_download_count()
        doc.refresh_from_db()
        assert doc.download_count == 1


@pytest.mark.django_db
class TestSellerProfile:
    """Tests for SellerProfile model."""

    def test_create_profile(self, user, seller_profile_factory):
        """Test seller profile creation."""
        profile = seller_profile_factory(user, display_name="John Seller")
        assert profile.display_name == "John Seller"
        assert profile.user_id == user.id
        assert profile.is_active is True

    def test_working_days_list(self, user, seller_profile_factory):
        """Test get_working_days_list method."""
        profile = seller_profile_factory(user, working_days="1,2,3,4,5")
        assert profile.get_working_days_list() == [1, 2, 3, 4, 5]

        profile.working_days = "1,3,5"
        assert profile.get_working_days_list() == [1, 3, 5]
