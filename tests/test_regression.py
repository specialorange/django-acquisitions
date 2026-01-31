"""
Regression tests for django-acquisitions.

These tests ensure that critical functionality doesn't break between releases.
Each test documents a specific behavior that must be maintained.
"""

import pytest
from django.db import IntegrityError
from django.utils import timezone

from acquisitions.models import (
    CampaignEnrollment,
    CampaignStep,
    Category,
    Industry,
    MarketingDocument,
    OutreachCampaign,
    ProspectiveClient,
    ProspectiveClientContact,
    SellerProfile,
    Touchpoint,
)


# =============================================================================
# Model Field Regression Tests
# =============================================================================


@pytest.mark.django_db
class TestProspectiveClientFieldRegression:
    """Ensure ProspectiveClient fields maintain expected behavior."""

    def test_uuid_is_auto_generated(self, prospective_client_factory):
        """UUID should be automatically generated on creation."""
        pc = prospective_client_factory()
        assert pc.uuid is not None
        assert len(str(pc.uuid)) == 36  # UUID format

    def test_uuid_is_unique(self, prospective_client_factory):
        """Each ProspectiveClient must have a unique UUID."""
        pc1 = prospective_client_factory()
        pc2 = prospective_client_factory()
        assert pc1.uuid != pc2.uuid

    def test_default_status_is_new(self, prospective_client_factory):
        """Default status should be NEW."""
        pc = prospective_client_factory()
        assert pc.status == ProspectiveClient.Status.NEW

    def test_default_source_is_other(self):
        """Default source should be OTHER when not specified."""
        pc = ProspectiveClient.objects.create(company_name="Test")
        assert pc.source == ProspectiveClient.Source.OTHER

    def test_default_priority_is_5(self):
        """Default priority should be 5 (middle of 1-10 range)."""
        pc = ProspectiveClient.objects.create(company_name="Test")
        assert pc.priority == 5

    def test_default_score_is_0(self):
        """Default score should be 0."""
        pc = ProspectiveClient.objects.create(company_name="Test")
        assert pc.score == 0

    def test_timestamps_auto_set(self):
        """created_at and updated_at should be automatically set."""
        pc = ProspectiveClient.objects.create(company_name="Test")
        assert pc.created_at is not None
        assert pc.updated_at is not None

    def test_updated_at_changes_on_save(self):
        """updated_at should change when model is saved."""
        pc = ProspectiveClient.objects.create(company_name="Test")
        original_updated = pc.updated_at

        pc.company_name = "Updated"
        pc.save()

        assert pc.updated_at > original_updated


@pytest.mark.django_db
class TestProspectiveClientStatusRegression:
    """Ensure status-related logic works correctly."""

    def test_all_status_choices_exist(self):
        """All expected status choices must be available."""
        expected = {"new", "contacted", "qualified", "proposal", "negotiation", "won", "lost", "dormant"}
        actual = {choice[0] for choice in ProspectiveClient.Status.choices}
        assert expected == actual

    def test_is_active_for_pipeline_statuses(self):
        """is_active should be True for pipeline statuses."""
        active_statuses = [
            ProspectiveClient.Status.NEW,
            ProspectiveClient.Status.CONTACTED,
            ProspectiveClient.Status.QUALIFIED,
            ProspectiveClient.Status.PROPOSAL,
            ProspectiveClient.Status.NEGOTIATION,
        ]
        for status in active_statuses:
            pc = ProspectiveClient(company_name="Test", status=status)
            assert pc.is_active is True, f"Status {status} should be active"

    def test_is_active_false_for_terminal_statuses(self):
        """is_active should be False for terminal statuses."""
        terminal_statuses = [
            ProspectiveClient.Status.WON,
            ProspectiveClient.Status.LOST,
            ProspectiveClient.Status.DORMANT,
        ]
        for status in terminal_statuses:
            pc = ProspectiveClient(company_name="Test", status=status)
            assert pc.is_active is False, f"Status {status} should not be active"


@pytest.mark.django_db
class TestProspectiveClientConversionRegression:
    """Ensure conversion logic works correctly."""

    def test_is_converted_requires_both_status_and_timestamp(self, prospective_client_factory):
        """is_converted should only be True when BOTH status=WON AND converted_at is set."""
        pc = prospective_client_factory(status=ProspectiveClient.Status.WON)
        # Status is WON but converted_at is None
        assert pc.is_converted is False

        pc.converted_at = timezone.now()
        assert pc.is_converted is True

    def test_mark_converted_sets_all_fields(self, prospective_client_factory):
        """mark_converted should set status, converted_at, and converted_to_id."""
        pc = prospective_client_factory()
        pc.mark_converted(customer_id=999)

        assert pc.status == ProspectiveClient.Status.WON
        assert pc.converted_at is not None
        assert pc.converted_to_id == 999

    def test_mark_converted_without_customer_id(self, prospective_client_factory):
        """mark_converted should work without customer_id."""
        pc = prospective_client_factory()
        pc.mark_converted()

        assert pc.status == ProspectiveClient.Status.WON
        assert pc.converted_at is not None
        assert pc.converted_to_id is None


# =============================================================================
# Relationship Regression Tests
# =============================================================================


@pytest.mark.django_db
class TestIndustryRelationshipRegression:
    """Ensure Industry relationships work correctly."""

    def test_industry_can_be_null(self):
        """ProspectiveClient should be creatable without industry."""
        pc = ProspectiveClient.objects.create(company_name="Test", industry=None)
        assert pc.industry is None

    def test_industry_set_null_on_delete(self, industry_factory):
        """Deleting Industry should SET NULL on ProspectiveClient."""
        industry = industry_factory(name="ToDelete")
        pc = ProspectiveClient.objects.create(company_name="Test", industry=industry)

        industry.delete()
        pc.refresh_from_db()

        assert pc.industry is None

    def test_reverse_relation_name(self, industry_factory, prospective_client_factory):
        """Industry.prospective_clients should access related objects."""
        industry = industry_factory(name="Tech")
        pc = prospective_client_factory(industry=industry)

        assert pc in industry.prospective_clients.all()


@pytest.mark.django_db
class TestCategoryRelationshipRegression:
    """Ensure Category M2M relationships work correctly."""

    def test_categories_can_be_empty(self, prospective_client_factory):
        """ProspectiveClient can exist without categories."""
        pc = prospective_client_factory()
        assert pc.categories.count() == 0

    def test_multiple_categories_allowed(self, prospective_client_factory, category_factory):
        """ProspectiveClient can have multiple categories."""
        pc = prospective_client_factory()
        cat1 = category_factory(name="Cat1")
        cat2 = category_factory(name="Cat2")
        cat3 = category_factory(name="Cat3")

        pc.categories.add(cat1, cat2, cat3)

        assert pc.categories.count() == 3

    def test_category_reverse_relation(self, prospective_client_factory, category_factory):
        """Category.prospective_clients should access related objects."""
        category = category_factory(name="VIP")
        pc1 = prospective_client_factory(company_name="A")
        pc2 = prospective_client_factory(company_name="B")

        pc1.categories.add(category)
        pc2.categories.add(category)

        assert category.prospective_clients.count() == 2


# =============================================================================
# Contact Regression Tests
# =============================================================================


@pytest.mark.django_db
class TestContactPrimaryRegression:
    """Ensure primary contact logic works correctly."""

    def test_setting_primary_unsets_other_primaries(self, prospective_client, contact_factory):
        """Setting is_primary=True should unset other primary contacts."""
        contact1 = contact_factory(prospective_client, first_name="First", is_primary=True)
        assert contact1.is_primary is True

        contact2 = contact_factory(prospective_client, first_name="Second", is_primary=True)
        assert contact2.is_primary is True

        contact1.refresh_from_db()
        assert contact1.is_primary is False

    def test_multiple_non_primary_allowed(self, prospective_client, contact_factory):
        """Multiple non-primary contacts should be allowed."""
        contact1 = contact_factory(prospective_client, first_name="First", is_primary=False)
        contact2 = contact_factory(prospective_client, first_name="Second", is_primary=False)
        contact3 = contact_factory(prospective_client, first_name="Third", is_primary=False)

        assert contact1.is_primary is False
        assert contact2.is_primary is False
        assert contact3.is_primary is False

    def test_contact_deleted_with_prospective_client(self, prospective_client_factory, contact_factory):
        """Contacts should be deleted when ProspectiveClient is deleted (CASCADE)."""
        pc = prospective_client_factory()
        contact = contact_factory(pc, first_name="Test")
        contact_id = contact.id

        pc.delete()

        assert not ProspectiveClientContact.objects.filter(id=contact_id).exists()


# =============================================================================
# Campaign Regression Tests
# =============================================================================


@pytest.mark.django_db
class TestCampaignEnrollmentRegression:
    """Ensure campaign enrollment logic works correctly."""

    def test_unique_enrollment_constraint(self, prospective_client, campaign):
        """A ProspectiveClient can only be enrolled once per campaign."""
        CampaignEnrollment.objects.create(prospective_client=prospective_client, campaign=campaign)

        with pytest.raises(IntegrityError):
            CampaignEnrollment.objects.create(prospective_client=prospective_client, campaign=campaign)

    def test_enrollment_defaults(self, prospective_client, campaign):
        """Enrollment should have correct defaults."""
        enrollment = CampaignEnrollment.objects.create(
            prospective_client=prospective_client,
            campaign=campaign,
        )

        assert enrollment.current_step == 0
        assert enrollment.is_active is True
        assert enrollment.completed_at is None


@pytest.mark.django_db
class TestCampaignStepRegression:
    """Ensure campaign step logic works correctly."""

    def test_step_order_unique_within_campaign(self, campaign_factory, campaign_step_factory):
        """step_order should be unique within a campaign."""
        campaign = campaign_factory()
        campaign_step_factory(campaign, step_order=0)

        with pytest.raises(IntegrityError):
            campaign_step_factory(campaign, step_order=0)

    def test_step_order_can_repeat_across_campaigns(self, campaign_factory, campaign_step_factory):
        """step_order can repeat in different campaigns."""
        campaign1 = campaign_factory(name="Campaign 1")
        campaign2 = campaign_factory(name="Campaign 2")

        step1 = campaign_step_factory(campaign1, step_order=0)
        step2 = campaign_step_factory(campaign2, step_order=0)

        assert step1.step_order == step2.step_order == 0

    def test_total_delay_hours_calculation(self, campaign_factory, campaign_step_factory):
        """total_delay_hours should correctly calculate from days and hours."""
        campaign = campaign_factory()
        step = campaign_step_factory(campaign, delay_days=3, delay_hours=12, step_order=0)

        assert step.total_delay_hours == (3 * 24) + 12  # 84 hours


# =============================================================================
# Touchpoint Regression Tests
# =============================================================================


@pytest.mark.django_db
class TestTouchpointRegression:
    """Ensure touchpoint logic works correctly."""

    def test_touchpoint_ordering_by_occurred_at_desc(self, prospective_client, touchpoint_factory):
        """Touchpoints should be ordered by occurred_at descending."""
        now = timezone.now()
        tp_old = touchpoint_factory(prospective_client, occurred_at=now - timezone.timedelta(days=10))
        tp_mid = touchpoint_factory(prospective_client, occurred_at=now - timezone.timedelta(days=5))
        tp_new = touchpoint_factory(prospective_client, occurred_at=now)

        touchpoints = list(prospective_client.touchpoints.all())
        assert touchpoints[0] == tp_new
        assert touchpoints[1] == tp_mid
        assert touchpoints[2] == tp_old

    def test_touchpoint_contact_set_null_on_delete(self, prospective_client, contact_factory, touchpoint_factory):
        """Deleting a contact should SET NULL on touchpoints."""
        contact = contact_factory(prospective_client, first_name="Test")
        touchpoint = touchpoint_factory(prospective_client, contact=contact)

        contact.delete()
        touchpoint.refresh_from_db()

        assert touchpoint.contact is None


# =============================================================================
# Marketing Document Regression Tests
# =============================================================================


@pytest.mark.django_db
class TestMarketingDocumentRegression:
    """Ensure marketing document logic works correctly."""

    def test_increment_view_count_atomic(self):
        """increment_view_count should work atomically."""
        doc = MarketingDocument.objects.create(
            name="Test",
            document_type=MarketingDocument.DocumentType.BROCHURE,
        )
        initial_count = doc.view_count

        # Simulate concurrent increments
        for _ in range(10):
            doc.increment_view_count()

        doc.refresh_from_db()
        assert doc.view_count == initial_count + 10

    def test_increment_download_count_atomic(self):
        """increment_download_count should work atomically."""
        doc = MarketingDocument.objects.create(
            name="Test",
            document_type=MarketingDocument.DocumentType.BROCHURE,
        )
        initial_count = doc.download_count

        for _ in range(5):
            doc.increment_download_count()

        doc.refresh_from_db()
        assert doc.download_count == initial_count + 5


# =============================================================================
# Seller Profile Regression Tests
# =============================================================================


@pytest.mark.django_db
class TestSellerProfileRegression:
    """Ensure seller profile logic works correctly."""

    def test_user_id_unique_constraint(self, user, seller_profile_factory):
        """user_id must be unique across seller profiles."""
        seller_profile_factory(user)

        with pytest.raises(IntegrityError):
            SellerProfile.objects.create(
                user_id=user.id,
                display_name="Duplicate",
                email="dup@example.com",
            )

    def test_working_days_list_parsing(self, user, seller_profile_factory):
        """get_working_days_list should correctly parse comma-separated days."""
        profile = seller_profile_factory(user, working_days="1,3,5")
        assert profile.get_working_days_list() == [1, 3, 5]

        profile.working_days = "1,2,3,4,5,6,7"
        assert profile.get_working_days_list() == [1, 2, 3, 4, 5, 6, 7]

        profile.working_days = "2"
        assert profile.get_working_days_list() == [2]


# =============================================================================
# Ordering Regression Tests
# =============================================================================


@pytest.mark.django_db
class TestModelOrderingRegression:
    """Ensure model ordering is maintained."""

    def test_prospective_client_ordering(self, prospective_client_factory):
        """ProspectiveClients should be ordered by priority, -score, -created_at."""
        pc1 = prospective_client_factory(company_name="Low Priority", priority=10, score=50)
        pc2 = prospective_client_factory(company_name="High Priority Low Score", priority=1, score=50)
        pc3 = prospective_client_factory(company_name="High Priority High Score", priority=1, score=100)

        ordered = list(ProspectiveClient.objects.all())
        assert ordered[0] == pc3  # priority=1, highest score
        assert ordered[1] == pc2  # priority=1, lower score
        assert ordered[2] == pc1  # priority=10

    def test_category_ordering(self, category_factory):
        """Categories should be ordered by name."""
        cat_z = category_factory(name="Zebra")
        cat_a = category_factory(name="Apple")
        cat_m = category_factory(name="Mango")

        ordered = list(Category.objects.all())
        assert ordered[0] == cat_a
        assert ordered[1] == cat_m
        assert ordered[2] == cat_z

    def test_industry_ordering(self, industry_factory):
        """Industries should be ordered by name."""
        ind_z = industry_factory(name="Zoology")
        ind_a = industry_factory(name="Agriculture")
        ind_m = industry_factory(name="Manufacturing")

        ordered = list(Industry.objects.all())
        assert ordered[0] == ind_a
        assert ordered[1] == ind_m
        assert ordered[2] == ind_z

    def test_campaign_step_ordering(self, campaign_factory, campaign_step_factory):
        """CampaignSteps should be ordered by step_order."""
        campaign = campaign_factory()
        step3 = campaign_step_factory(campaign, step_order=2)
        step1 = campaign_step_factory(campaign, step_order=0)
        step2 = campaign_step_factory(campaign, step_order=1)

        ordered = list(campaign.steps.all())
        assert ordered[0] == step1
        assert ordered[1] == step2
        assert ordered[2] == step3
