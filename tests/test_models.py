"""
Model tests for django-acquisitions.
"""

import pytest
from django.utils import timezone

from acquisitions.models import (
    CampaignEnrollment,
    Category,
    Industry,
    MarketingDocument,
    OutreachCampaign,
    ProspectiveClient,
    ProspectiveClientContact,
    SellerProfile,
    Touchpoint,
)


@pytest.mark.django_db
class TestCategory:
    """Tests for Category model."""

    def test_create_category(self, category_factory):
        """Test basic category creation."""
        category = category_factory(name="Enterprise", color="#3b82f6")
        assert category.name == "Enterprise"
        assert category.color == "#3b82f6"
        assert category.is_active is True

    def test_category_str(self, category_factory):
        """Test category string representation."""
        category = category_factory(name="Urgent")
        assert str(category) == "Urgent"

    def test_category_ordering(self, category_factory):
        """Test categories are ordered by name."""
        cat_z = category_factory(name="Zzz Category")
        cat_a = category_factory(name="Aaa Category")
        cat_m = category_factory(name="Mmm Category")

        categories = list(Category.objects.all())
        assert categories[0] == cat_a
        assert categories[1] == cat_m
        assert categories[2] == cat_z


@pytest.mark.django_db
class TestIndustry:
    """Tests for Industry model."""

    def test_create_industry(self, industry_factory):
        """Test basic industry creation."""
        industry = industry_factory(name="Healthcare", description="Medical and health services")
        assert industry.name == "Healthcare"
        assert industry.description == "Medical and health services"
        assert industry.is_active is True

    def test_industry_str(self, industry_factory):
        """Test industry string representation."""
        industry = industry_factory(name="Finance")
        assert str(industry) == "Finance"

    def test_industry_unique_name(self, industry_factory):
        """Test industry name must be unique."""
        industry_factory(name="Technology")
        with pytest.raises(Exception):
            industry_factory(name="Technology")


@pytest.mark.django_db
class TestProspectiveClient:
    """Tests for ProspectiveClient model."""

    def test_create_prospective_client(self, prospective_client_factory):
        """Test basic prospective client creation."""
        pc = prospective_client_factory(company_name="Acme Corp")
        assert pc.company_name == "Acme Corp"
        assert pc.status == ProspectiveClient.Status.NEW
        assert pc.uuid is not None

    def test_prospective_client_is_active(self, prospective_client_factory):
        """Test is_active property."""
        active_pc = prospective_client_factory(status=ProspectiveClient.Status.CONTACTED)
        assert active_pc.is_active is True

        won_pc = prospective_client_factory(status=ProspectiveClient.Status.WON)
        assert won_pc.is_active is False

        lost_pc = prospective_client_factory(status=ProspectiveClient.Status.LOST)
        assert lost_pc.is_active is False

    def test_prospective_client_is_converted(self, prospective_client_factory):
        """Test is_converted property."""
        pc = prospective_client_factory()
        assert pc.is_converted is False

        pc.status = ProspectiveClient.Status.WON
        pc.converted_at = timezone.now()
        pc.converted_to_id = 123
        pc.save()

        assert pc.is_converted is True

    def test_mark_converted(self, prospective_client_factory):
        """Test mark_converted method."""
        pc = prospective_client_factory()
        pc.mark_converted(customer_id=456)

        assert pc.status == ProspectiveClient.Status.WON
        assert pc.converted_at is not None
        assert pc.converted_to_id == 456

    def test_prospective_client_ordering(self, prospective_client_factory):
        """Test prospective client ordering by priority and score."""
        pc1 = prospective_client_factory(company_name="Low Priority", priority=10, score=50)
        pc2 = prospective_client_factory(company_name="High Priority", priority=1, score=50)
        pc3 = prospective_client_factory(company_name="High Score", priority=1, score=100)

        pcs = list(ProspectiveClient.objects.all())
        assert pcs[0] == pc3  # Same priority, higher score
        assert pcs[1] == pc2  # Same priority, lower score
        assert pcs[2] == pc1  # Lower priority

    def test_prospective_client_with_industry(self, prospective_client_factory, industry_factory):
        """Test prospective client with industry FK."""
        industry = industry_factory(name="Transportation")
        pc = prospective_client_factory(company_name="Trucking Co", industry=industry)

        assert pc.industry == industry
        assert pc.industry.name == "Transportation"
        assert pc in industry.prospective_clients.all()

    def test_prospective_client_with_categories(self, prospective_client_factory, category_factory):
        """Test prospective client with multiple categories (M2M)."""
        cat1 = category_factory(name="Enterprise")
        cat2 = category_factory(name="High Value")
        cat3 = category_factory(name="Urgent")

        pc = prospective_client_factory(company_name="Big Corp")
        pc.categories.add(cat1, cat2)

        assert pc.categories.count() == 2
        assert cat1 in pc.categories.all()
        assert cat2 in pc.categories.all()
        assert cat3 not in pc.categories.all()

    def test_prospective_client_categories_reverse_relation(self, prospective_client_factory, category_factory):
        """Test accessing prospective clients from category."""
        category = category_factory(name="VIP")
        pc1 = prospective_client_factory(company_name="Company A")
        pc2 = prospective_client_factory(company_name="Company B")
        pc3 = prospective_client_factory(company_name="Company C")

        pc1.categories.add(category)
        pc2.categories.add(category)

        assert category.prospective_clients.count() == 2
        assert pc1 in category.prospective_clients.all()
        assert pc2 in category.prospective_clients.all()
        assert pc3 not in category.prospective_clients.all()

    def test_prospective_client_without_industry(self, prospective_client_factory):
        """Test prospective client can exist without industry."""
        pc = prospective_client_factory(company_name="No Industry Co", industry=None)
        assert pc.industry is None

    def test_prospective_client_industry_set_null_on_delete(self, prospective_client_factory, industry_factory):
        """Test prospective_client.industry is set to NULL when industry is deleted."""
        industry = industry_factory(name="Obsolete Industry")
        pc = prospective_client_factory(company_name="Test Co", industry=industry)

        industry.delete()
        pc.refresh_from_db()

        assert pc.industry is None


@pytest.mark.django_db
class TestProspectiveClientContact:
    """Tests for ProspectiveClientContact model."""

    def test_create_contact(self, prospective_client, contact_factory):
        """Test contact creation."""
        contact = contact_factory(prospective_client, first_name="Jane", last_name="Smith")
        assert contact.full_name == "Jane Smith"
        assert contact.prospective_client == prospective_client

    def test_primary_contact(self, prospective_client, contact_factory):
        """Test primary contact handling."""
        contact1 = contact_factory(prospective_client, first_name="John", is_primary=True)
        assert contact1.is_primary is True

        contact2 = contact_factory(prospective_client, first_name="Jane", is_primary=True)
        assert contact2.is_primary is True

        # First contact should no longer be primary
        contact1.refresh_from_db()
        assert contact1.is_primary is False

    def test_contact_ordering(self, prospective_client, contact_factory):
        """Test contact ordering (primary first, then by last name)."""
        contact1 = contact_factory(prospective_client, first_name="Zack", last_name="Adams", is_primary=False)
        contact2 = contact_factory(prospective_client, first_name="Alice", last_name="Brown", is_primary=True)
        contact3 = contact_factory(prospective_client, first_name="Bob", last_name="Cooper", is_primary=False)

        contacts = list(prospective_client.contacts.all())
        assert contacts[0] == contact2  # Primary first
        assert contacts[1] == contact1  # Then by last name: Adams
        assert contacts[2] == contact3  # Then Cooper


@pytest.mark.django_db
class TestTouchpoint:
    """Tests for Touchpoint model."""

    def test_create_touchpoint(self, prospective_client, touchpoint_factory):
        """Test touchpoint creation."""
        touchpoint = touchpoint_factory(
            prospective_client,
            touchpoint_type=Touchpoint.TouchpointType.EMAIL,
            subject="Introduction",
        )
        assert touchpoint.prospective_client == prospective_client
        assert touchpoint.touchpoint_type == "email"
        assert touchpoint.subject == "Introduction"

    def test_touchpoint_ordering(self, prospective_client, touchpoint_factory):
        """Test touchpoints ordered by occurred_at descending."""
        now = timezone.now()
        tp1 = touchpoint_factory(prospective_client, occurred_at=now - timezone.timedelta(days=2))
        tp2 = touchpoint_factory(prospective_client, occurred_at=now)
        tp3 = touchpoint_factory(prospective_client, occurred_at=now - timezone.timedelta(days=1))

        touchpoints = list(prospective_client.touchpoints.all())
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

    def test_enroll_prospective_client(self, prospective_client, campaign):
        """Test enrolling a prospective client in a campaign."""
        enrollment = CampaignEnrollment.objects.create(
            prospective_client=prospective_client,
            campaign=campaign,
        )
        assert enrollment.is_active is True
        assert enrollment.current_step == 0

    def test_unique_enrollment(self, prospective_client, campaign):
        """Test that a prospective client can only be enrolled once in a campaign."""
        CampaignEnrollment.objects.create(prospective_client=prospective_client, campaign=campaign)

        with pytest.raises(Exception):  # IntegrityError
            CampaignEnrollment.objects.create(prospective_client=prospective_client, campaign=campaign)


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


# Test backwards compatibility aliases
@pytest.mark.django_db
class TestBackwardsCompatibility:
    """Tests for backwards compatibility aliases."""

    def test_lead_alias(self, prospective_client_factory):
        """Test Lead is an alias for ProspectiveClient."""
        from acquisitions.models import Lead

        pc = prospective_client_factory(company_name="Test")
        assert isinstance(pc, Lead)
        assert Lead is ProspectiveClient

    def test_lead_contact_alias(self, prospective_client, contact_factory):
        """Test LeadContact is an alias for ProspectiveClientContact."""
        from acquisitions.models import LeadContact

        contact = contact_factory(prospective_client, first_name="Test")
        assert isinstance(contact, LeadContact)
        assert LeadContact is ProspectiveClientContact
