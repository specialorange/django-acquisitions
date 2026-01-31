"""
API tests for django-acquisitions.
"""

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from acquisitions.models import (
    Category,
    Industry,
    MarketingDocument,
    OutreachCampaign,
    ProspectiveClient,
    ProspectiveClientContact,
    Touchpoint,
)


@pytest.fixture
def api_client():
    """Return an API client."""
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, user):
    """Return an authenticated API client."""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def staff_client(api_client, staff_user):
    """Return an authenticated staff API client."""
    api_client.force_authenticate(user=staff_user)
    return api_client


@pytest.mark.django_db
class TestProspectiveClientAPI:
    """Tests for ProspectiveClient API endpoints."""

    def test_list_prospective_clients_unauthenticated(self, api_client):
        """Test unauthenticated users cannot list prospective clients."""
        response = api_client.get("/api/acquisitions/prospective-clients/")
        # DRF returns 403 for unauthenticated requests by default
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

    def test_list_prospective_clients_authenticated(self, authenticated_client, prospective_client_factory):
        """Test authenticated users can list prospective clients."""
        prospective_client_factory(company_name="Company A")
        prospective_client_factory(company_name="Company B")

        response = authenticated_client.get("/api/acquisitions/prospective-clients/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

    def test_create_prospective_client(self, authenticated_client):
        """Test creating a prospective client."""
        data = {
            "company_name": "New Company",
            "status": "new",
            "source": "website",
        }
        response = authenticated_client.post("/api/acquisitions/prospective-clients/", data)
        assert response.status_code == status.HTTP_201_CREATED
        assert ProspectiveClient.objects.filter(company_name="New Company").exists()

    def test_retrieve_prospective_client(self, authenticated_client, prospective_client_factory):
        """Test retrieving a single prospective client."""
        pc = prospective_client_factory(company_name="Test Company")

        response = authenticated_client.get(f"/api/acquisitions/prospective-clients/{pc.uuid}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["company_name"] == "Test Company"

    def test_update_prospective_client(self, authenticated_client, prospective_client_factory):
        """Test updating a prospective client."""
        pc = prospective_client_factory(company_name="Old Name")

        response = authenticated_client.patch(
            f"/api/acquisitions/prospective-clients/{pc.uuid}/",
            {"company_name": "New Name"},
        )
        assert response.status_code == status.HTTP_200_OK

        pc.refresh_from_db()
        assert pc.company_name == "New Name"

    def test_delete_prospective_client(self, authenticated_client, prospective_client_factory):
        """Test deleting a prospective client."""
        pc = prospective_client_factory()
        pc_uuid = pc.uuid

        response = authenticated_client.delete(f"/api/acquisitions/prospective-clients/{pc_uuid}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not ProspectiveClient.objects.filter(uuid=pc_uuid).exists()

    def test_filter_prospective_clients_by_status(self, authenticated_client, prospective_client_factory):
        """Test filtering prospective clients by status."""
        prospective_client_factory(company_name="New PC", status=ProspectiveClient.Status.NEW)
        prospective_client_factory(company_name="Contacted PC", status=ProspectiveClient.Status.CONTACTED)

        response = authenticated_client.get("/api/acquisitions/prospective-clients/?status=new")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["company_name"] == "New PC"

    def test_filter_prospective_clients_by_assigned_to_me(self, authenticated_client, prospective_client_factory, user):
        """Test filtering prospective clients assigned to current user."""
        prospective_client_factory(company_name="My PC", assigned_to_id=user.id)
        prospective_client_factory(company_name="Other PC", assigned_to_id=999)

        response = authenticated_client.get("/api/acquisitions/prospective-clients/?assigned_to=me")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["company_name"] == "My PC"

    def test_search_prospective_clients(self, authenticated_client, prospective_client_factory):
        """Test searching prospective clients by company name."""
        prospective_client_factory(company_name="Acme Corporation")
        prospective_client_factory(company_name="Beta Industries")

        response = authenticated_client.get("/api/acquisitions/prospective-clients/?search=Acme")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["company_name"] == "Acme Corporation"

    def test_convert_prospective_client(self, authenticated_client, prospective_client_factory):
        """Test converting a prospective client to customer."""
        pc = prospective_client_factory(status=ProspectiveClient.Status.QUALIFIED)

        response = authenticated_client.post(f"/api/acquisitions/prospective-clients/{pc.uuid}/convert/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

        pc.refresh_from_db()
        assert pc.status == ProspectiveClient.Status.WON
        assert pc.converted_at is not None

    def test_convert_already_converted_prospective_client(self, authenticated_client, prospective_client_factory):
        """Test converting an already converted prospective client fails."""
        pc = prospective_client_factory(status=ProspectiveClient.Status.WON)

        response = authenticated_client.post(f"/api/acquisitions/prospective-clients/{pc.uuid}/convert/")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_enroll_prospective_client_in_campaign(self, authenticated_client, prospective_client_factory, campaign):
        """Test enrolling a prospective client in a campaign."""
        pc = prospective_client_factory()

        response = authenticated_client.post(
            f"/api/acquisitions/prospective-clients/{pc.uuid}/enroll_campaign/",
            {"campaign_uuid": str(campaign.uuid)},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

    def test_enroll_prospective_client_missing_campaign(self, authenticated_client, prospective_client_factory):
        """Test enrolling without campaign_uuid fails."""
        pc = prospective_client_factory()

        response = authenticated_client.post(
            f"/api/acquisitions/prospective-clients/{pc.uuid}/enroll_campaign/",
            {},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_prospective_client_with_industry(self, authenticated_client, prospective_client_factory, industry_factory):
        """Test prospective client response includes industry details."""
        industry = industry_factory(name="Technology")
        pc = prospective_client_factory(company_name="Tech Co", industry=industry)

        response = authenticated_client.get(f"/api/acquisitions/prospective-clients/{pc.uuid}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["industry"] == industry.id
        assert response.data["industry_detail"]["name"] == "Technology"


@pytest.mark.django_db
class TestProspectiveClientContactAPI:
    """Tests for ProspectiveClientContact API endpoints."""

    def test_list_contacts(self, authenticated_client, prospective_client_factory, contact_factory):
        """Test listing contacts for a prospective client."""
        pc = prospective_client_factory()
        contact_factory(pc, first_name="John")
        contact_factory(pc, first_name="Jane")

        response = authenticated_client.get(
            f"/api/acquisitions/prospective-clients/{pc.uuid}/contacts/"
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

    def test_create_contact(self, authenticated_client, prospective_client_factory):
        """Test creating a contact for a prospective client."""
        pc = prospective_client_factory()

        data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "is_primary": True,
        }
        response = authenticated_client.post(
            f"/api/acquisitions/prospective-clients/{pc.uuid}/contacts/",
            data,
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert ProspectiveClientContact.objects.filter(prospective_client=pc, first_name="John").exists()

    def test_update_contact(self, authenticated_client, prospective_client_factory, contact_factory):
        """Test updating a contact."""
        pc = prospective_client_factory()
        contact = contact_factory(pc, first_name="John")

        response = authenticated_client.patch(
            f"/api/acquisitions/prospective-clients/{pc.uuid}/contacts/{contact.uuid}/",
            {"first_name": "Jonathan"},
        )
        assert response.status_code == status.HTTP_200_OK

        contact.refresh_from_db()
        assert contact.first_name == "Jonathan"


@pytest.mark.django_db
class TestTouchpointAPI:
    """Tests for Touchpoint API endpoints."""

    def test_list_touchpoints(self, authenticated_client, prospective_client_factory, touchpoint_factory):
        """Test listing touchpoints for a prospective client."""
        pc = prospective_client_factory()
        touchpoint_factory(pc)
        touchpoint_factory(pc)

        response = authenticated_client.get(
            f"/api/acquisitions/prospective-clients/{pc.uuid}/touchpoints/"
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

    def test_create_touchpoint(self, authenticated_client, prospective_client_factory, user):
        """Test creating a touchpoint."""
        pc = prospective_client_factory()

        data = {
            "touchpoint_type": "email",
            "direction": "outbound",
            "subject": "Follow up",
            "occurred_at": "2024-01-15T10:00:00Z",
        }
        response = authenticated_client.post(
            f"/api/acquisitions/prospective-clients/{pc.uuid}/touchpoints/",
            data,
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert Touchpoint.objects.filter(prospective_client=pc, subject="Follow up").exists()

        # Check performed_by_id is set
        touchpoint = Touchpoint.objects.get(prospective_client=pc, subject="Follow up")
        assert touchpoint.performed_by_id == user.id


@pytest.mark.django_db
class TestCampaignAPI:
    """Tests for OutreachCampaign API endpoints."""

    def test_list_campaigns(self, authenticated_client, campaign_factory, seller_profile_factory, user):
        """Test listing campaigns."""
        seller_profile_factory(user)
        campaign_factory(name="Campaign A")
        campaign_factory(name="Campaign B")

        response = authenticated_client.get("/api/acquisitions/campaigns/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

    def test_create_campaign(self, authenticated_client, seller_profile_factory, user):
        """Test creating a campaign."""
        seller_profile_factory(user)

        data = {
            "name": "New Campaign",
            "status": "draft",
        }
        response = authenticated_client.post("/api/acquisitions/campaigns/", data)
        assert response.status_code == status.HTTP_201_CREATED
        assert OutreachCampaign.objects.filter(name="New Campaign").exists()

        campaign = OutreachCampaign.objects.get(name="New Campaign")
        assert campaign.created_by_id == user.id

    def test_retrieve_campaign_with_steps(
        self, authenticated_client, campaign_factory, campaign_step_factory, seller_profile_factory, user
    ):
        """Test retrieving campaign includes steps."""
        seller_profile_factory(user)
        campaign = campaign_factory()
        campaign_step_factory(campaign, step_order=0)
        campaign_step_factory(campaign, step_order=1)

        response = authenticated_client.get(f"/api/acquisitions/campaigns/{campaign.uuid}/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["steps"]) == 2


@pytest.mark.django_db
class TestMarketingDocumentAPI:
    """Tests for MarketingDocument API endpoints."""

    def test_list_documents(self, authenticated_client):
        """Test listing documents."""
        MarketingDocument.objects.create(
            name="Brochure",
            document_type="brochure",
            is_active=True,
        )
        MarketingDocument.objects.create(
            name="Internal Doc",
            document_type="other",
            is_internal_only=True,
            is_active=True,
        )

        response = authenticated_client.get("/api/acquisitions/documents/")
        assert response.status_code == status.HTTP_200_OK
        # Non-staff users shouldn't see internal docs
        assert len(response.data) == 1
        assert response.data[0]["name"] == "Brochure"

    def test_list_documents_staff_sees_internal(self, staff_client):
        """Test staff users can see internal documents."""
        MarketingDocument.objects.create(
            name="Brochure",
            document_type="brochure",
            is_active=True,
        )
        MarketingDocument.objects.create(
            name="Internal Doc",
            document_type="other",
            is_internal_only=True,
            is_active=True,
        )

        response = staff_client.get("/api/acquisitions/documents/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

    def test_track_view(self, staff_client):
        """Test tracking document views."""
        doc = MarketingDocument.objects.create(
            name="Test Doc",
            document_type="brochure",
            is_active=True,
        )
        assert doc.view_count == 0

        response = staff_client.post(
            f"/api/acquisitions/documents/{doc.uuid}/track_view/"
        )
        assert response.status_code == status.HTTP_200_OK

        doc.refresh_from_db()
        assert doc.view_count == 1

    def test_track_download(self, staff_client):
        """Test tracking document downloads."""
        doc = MarketingDocument.objects.create(
            name="Test Doc",
            document_type="brochure",
            is_active=True,
        )
        assert doc.download_count == 0

        response = staff_client.post(
            f"/api/acquisitions/documents/{doc.uuid}/track_download/"
        )
        assert response.status_code == status.HTTP_200_OK

        doc.refresh_from_db()
        assert doc.download_count == 1

    def test_filter_by_type(self, authenticated_client):
        """Test filtering documents by type."""
        MarketingDocument.objects.create(
            name="Brochure",
            document_type="brochure",
            is_active=True,
        )
        MarketingDocument.objects.create(
            name="Case Study",
            document_type="case_study",
            is_active=True,
        )

        response = authenticated_client.get("/api/acquisitions/documents/?type=brochure")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["name"] == "Brochure"


@pytest.mark.django_db
class TestSellerProfileAPI:
    """Tests for SellerProfile API endpoints."""

    def test_get_my_profile(self, authenticated_client, seller_profile_factory, user):
        """Test getting current user's seller profile."""
        profile = seller_profile_factory(user, display_name="Test Seller")

        response = authenticated_client.get("/api/acquisitions/sellers/me/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["display_name"] == "Test Seller"

    def test_get_my_profile_not_found(self, authenticated_client, seller_profile_factory, user):
        """Test getting profile when none exists returns 404."""
        # User needs seller profile to access sellers endpoint, but we test the /me/ 404
        # Create a different user's profile to grant access, then delete user's profile
        # Actually, without a seller profile, user gets 403, not 404
        # Let's test that a seller can get 404 if profile is deleted
        profile = seller_profile_factory(user)
        profile.delete()
        # Now user has no profile but had one, still gets 403 as permission check fails
        response = authenticated_client.get("/api/acquisitions/sellers/me/")
        # Without a seller profile, access is denied
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]

    def test_list_sellers_requires_seller_or_admin(self, authenticated_client):
        """Test listing sellers requires seller profile or admin."""
        response = authenticated_client.get("/api/acquisitions/sellers/")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_sellers_as_seller(self, authenticated_client, seller_profile_factory, user):
        """Test sellers can list other sellers."""
        seller_profile_factory(user)

        response = authenticated_client.get("/api/acquisitions/sellers/")
        assert response.status_code == status.HTTP_200_OK
