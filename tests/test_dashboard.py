"""
Tests for dashboard service and API.
"""

import pytest
from datetime import timedelta
from django.utils import timezone

from acquisitions.models import (
    CampaignEnrollment,
    OutreachCampaign,
    ProspectiveClient,
    Touchpoint,
)
from acquisitions.services.dashboard import (
    get_activity_by_day,
    get_campaign_performance,
    get_conversion_funnel,
    get_full_dashboard,
    get_pipeline_summary,
    get_seller_performance,
    get_stale_prospects,
    get_unassigned_prospects,
    get_upcoming_outreach,
)


# =============================================================================
# Pipeline Summary Tests
# =============================================================================


@pytest.mark.django_db
class TestGetPipelineSummary:
    """Tests for get_pipeline_summary function."""

    def test_empty_pipeline(self):
        """Pipeline summary works with no prospective clients."""
        summary = get_pipeline_summary()

        assert summary["new"] == 0
        assert summary["contacted"] == 0
        assert summary["qualified"] == 0
        assert summary["proposal"] == 0
        assert summary["negotiation"] == 0
        assert summary["won"] == 0
        assert summary["lost"] == 0
        assert summary["dormant"] == 0
        assert summary["total"] == 0
        assert summary["active"] == 0
        assert summary["closed"] == 0

    def test_counts_by_status(self, prospective_client_factory):
        """Pipeline summary correctly counts by status."""
        prospective_client_factory(status=ProspectiveClient.Status.NEW)
        prospective_client_factory(status=ProspectiveClient.Status.NEW)
        prospective_client_factory(status=ProspectiveClient.Status.CONTACTED)
        prospective_client_factory(status=ProspectiveClient.Status.WON)

        summary = get_pipeline_summary()

        assert summary["new"] == 2
        assert summary["contacted"] == 1
        assert summary["won"] == 1
        assert summary["total"] == 4

    def test_active_count_excludes_terminal_statuses(self, prospective_client_factory):
        """Active count excludes won, lost, and dormant."""
        prospective_client_factory(status=ProspectiveClient.Status.NEW)
        prospective_client_factory(status=ProspectiveClient.Status.CONTACTED)
        prospective_client_factory(status=ProspectiveClient.Status.WON)
        prospective_client_factory(status=ProspectiveClient.Status.LOST)
        prospective_client_factory(status=ProspectiveClient.Status.DORMANT)

        summary = get_pipeline_summary()

        assert summary["active"] == 2  # new + contacted
        assert summary["closed"] == 2  # won + lost

    def test_all_statuses_included_in_active(self, prospective_client_factory):
        """All pipeline statuses are included in active count."""
        prospective_client_factory(status=ProspectiveClient.Status.NEW)
        prospective_client_factory(status=ProspectiveClient.Status.CONTACTED)
        prospective_client_factory(status=ProspectiveClient.Status.QUALIFIED)
        prospective_client_factory(status=ProspectiveClient.Status.PROPOSAL)
        prospective_client_factory(status=ProspectiveClient.Status.NEGOTIATION)

        summary = get_pipeline_summary()

        assert summary["active"] == 5


# =============================================================================
# Stale Prospects Tests
# =============================================================================


@pytest.mark.django_db
class TestGetStaleProspects:
    """Tests for get_stale_prospects function."""

    def test_no_touchpoints_is_stale(self, prospective_client_factory):
        """Prospects with no touchpoints are considered stale."""
        pc = prospective_client_factory(status=ProspectiveClient.Status.NEW)

        stale = list(get_stale_prospects(days=14))

        assert len(stale) == 1
        assert stale[0].id == pc.id

    def test_old_touchpoint_is_stale(self, prospective_client_factory, touchpoint_factory):
        """Prospects with only old touchpoints are stale."""
        pc = prospective_client_factory(status=ProspectiveClient.Status.CONTACTED)
        touchpoint_factory(pc, occurred_at=timezone.now() - timedelta(days=30))

        stale = list(get_stale_prospects(days=14))

        assert len(stale) == 1
        assert stale[0].id == pc.id

    def test_recent_touchpoint_not_stale(self, prospective_client_factory, touchpoint_factory):
        """Prospects with recent touchpoints are not stale."""
        pc = prospective_client_factory(status=ProspectiveClient.Status.CONTACTED)
        touchpoint_factory(pc, occurred_at=timezone.now() - timedelta(days=5))

        stale = list(get_stale_prospects(days=14))

        assert len(stale) == 0

    def test_terminal_status_not_included(self, prospective_client_factory):
        """Won/lost/dormant prospects are not included in stale list."""
        prospective_client_factory(status=ProspectiveClient.Status.WON)
        prospective_client_factory(status=ProspectiveClient.Status.LOST)
        prospective_client_factory(status=ProspectiveClient.Status.DORMANT)

        stale = list(get_stale_prospects(days=14))

        assert len(stale) == 0

    def test_stale_days_parameter(self, prospective_client_factory, touchpoint_factory):
        """stale_days parameter controls the threshold."""
        pc = prospective_client_factory(status=ProspectiveClient.Status.NEW)
        touchpoint_factory(pc, occurred_at=timezone.now() - timedelta(days=10))

        # With 14-day threshold, not stale
        assert len(list(get_stale_prospects(days=14))) == 0

        # With 7-day threshold, is stale
        assert len(list(get_stale_prospects(days=7))) == 1

    def test_limit_parameter(self, prospective_client_factory):
        """limit parameter restricts results."""
        for _ in range(10):
            prospective_client_factory(status=ProspectiveClient.Status.NEW)

        stale = list(get_stale_prospects(days=14, limit=5))

        assert len(stale) == 5

    def test_annotates_last_touchpoint(self, prospective_client_factory, touchpoint_factory):
        """Results include last_touchpoint annotation."""
        pc = prospective_client_factory(status=ProspectiveClient.Status.NEW)
        tp_time = timezone.now() - timedelta(days=20)
        touchpoint_factory(pc, occurred_at=tp_time)

        stale = list(get_stale_prospects(days=14))

        assert stale[0].last_touchpoint is not None

    def test_annotates_touchpoint_count(self, prospective_client_factory, touchpoint_factory):
        """Results include touchpoint_count annotation."""
        pc = prospective_client_factory(status=ProspectiveClient.Status.NEW)
        touchpoint_factory(pc, occurred_at=timezone.now() - timedelta(days=20))
        touchpoint_factory(pc, occurred_at=timezone.now() - timedelta(days=25))

        stale = list(get_stale_prospects(days=14))

        assert stale[0].touchpoint_count == 2


# =============================================================================
# Unassigned Prospects Tests
# =============================================================================


@pytest.mark.django_db
class TestGetUnassignedProspects:
    """Tests for get_unassigned_prospects function."""

    def test_returns_unassigned(self, prospective_client_factory):
        """Returns prospects with no assigned_to_id."""
        pc = prospective_client_factory(assigned_to_id=None)

        unassigned = list(get_unassigned_prospects())

        assert len(unassigned) == 1
        assert unassigned[0].id == pc.id

    def test_excludes_assigned(self, prospective_client_factory):
        """Excludes prospects with assigned_to_id."""
        prospective_client_factory(assigned_to_id=123)

        unassigned = list(get_unassigned_prospects())

        assert len(unassigned) == 0

    def test_excludes_terminal_statuses(self, prospective_client_factory):
        """Excludes won/lost/dormant even if unassigned."""
        prospective_client_factory(status=ProspectiveClient.Status.WON, assigned_to_id=None)
        prospective_client_factory(status=ProspectiveClient.Status.LOST, assigned_to_id=None)

        unassigned = list(get_unassigned_prospects())

        assert len(unassigned) == 0

    def test_limit_parameter(self, prospective_client_factory):
        """limit parameter restricts results."""
        for _ in range(10):
            prospective_client_factory(assigned_to_id=None)

        unassigned = list(get_unassigned_prospects(limit=3))

        assert len(unassigned) == 3


# =============================================================================
# Seller Performance Tests
# =============================================================================


@pytest.mark.django_db
class TestGetSellerPerformance:
    """Tests for get_seller_performance function."""

    def test_empty_without_sellers(self):
        """Returns empty list when no seller profiles exist."""
        performance = get_seller_performance()

        assert performance == []

    def test_counts_conversions(
        self, user, seller_profile_factory, prospective_client_factory
    ):
        """Counts conversions for each seller."""
        seller = seller_profile_factory(user)
        prospective_client_factory(
            status=ProspectiveClient.Status.WON,
            assigned_to_id=user.id,
            converted_at=timezone.now(),
        )
        prospective_client_factory(
            status=ProspectiveClient.Status.WON,
            assigned_to_id=user.id,
            converted_at=timezone.now(),
        )

        performance = get_seller_performance(days=30)

        assert len(performance) == 1
        assert performance[0]["conversions"] == 2

    def test_counts_active_prospects(
        self, user, seller_profile_factory, prospective_client_factory
    ):
        """Counts active prospects for each seller."""
        seller_profile_factory(user)
        prospective_client_factory(
            status=ProspectiveClient.Status.NEW, assigned_to_id=user.id
        )
        prospective_client_factory(
            status=ProspectiveClient.Status.CONTACTED, assigned_to_id=user.id
        )
        prospective_client_factory(
            status=ProspectiveClient.Status.WON, assigned_to_id=user.id
        )

        performance = get_seller_performance(days=30)

        assert performance[0]["active_prospects"] == 2  # excludes WON

    def test_counts_touchpoints(
        self, user, seller_profile_factory, prospective_client_factory, touchpoint_factory
    ):
        """Counts touchpoints performed by each seller."""
        seller_profile_factory(user)
        pc = prospective_client_factory()
        touchpoint_factory(pc)  # performed_by_id defaults to user.id
        touchpoint_factory(pc)

        performance = get_seller_performance(days=30)

        assert performance[0]["touchpoints"] == 2

    def test_days_parameter_filters_conversions(
        self, user, seller_profile_factory, prospective_client_factory
    ):
        """days parameter filters conversion date range."""
        seller_profile_factory(user)
        # Recent conversion
        prospective_client_factory(
            status=ProspectiveClient.Status.WON,
            assigned_to_id=user.id,
            converted_at=timezone.now(),
        )
        # Old conversion
        pc = prospective_client_factory(
            status=ProspectiveClient.Status.WON,
            assigned_to_id=user.id,
        )
        pc.converted_at = timezone.now() - timedelta(days=60)
        pc.save()

        performance = get_seller_performance(days=30)

        assert performance[0]["conversions"] == 1

    def test_sorted_by_conversions(
        self, user, staff_user, seller_profile_factory, prospective_client_factory
    ):
        """Results sorted by conversions descending."""
        seller1 = seller_profile_factory(user, display_name="Low Performer")
        seller2 = seller_profile_factory(staff_user, display_name="High Performer")

        # Give staff_user more conversions
        prospective_client_factory(
            status=ProspectiveClient.Status.WON,
            assigned_to_id=staff_user.id,
            converted_at=timezone.now(),
        )
        prospective_client_factory(
            status=ProspectiveClient.Status.WON,
            assigned_to_id=staff_user.id,
            converted_at=timezone.now(),
        )

        performance = get_seller_performance(days=30)

        assert performance[0]["display_name"] == "High Performer"
        assert performance[0]["conversions"] == 2


# =============================================================================
# Upcoming Outreach Tests
# =============================================================================


@pytest.mark.django_db
class TestGetUpcomingOutreach:
    """Tests for get_upcoming_outreach function."""

    def test_returns_scheduled_enrollments(
        self, prospective_client_factory, campaign_factory
    ):
        """Returns enrollments with upcoming scheduled steps."""
        pc = prospective_client_factory()
        campaign = campaign_factory()
        enrollment = CampaignEnrollment.objects.create(
            prospective_client=pc,
            campaign=campaign,
            is_active=True,
            next_step_scheduled_at=timezone.now() + timedelta(hours=12),
        )

        upcoming = list(get_upcoming_outreach(hours=48))

        assert len(upcoming) == 1
        assert upcoming[0].id == enrollment.id

    def test_excludes_past_scheduled(self, prospective_client_factory, campaign_factory):
        """Excludes enrollments with past scheduled time."""
        pc = prospective_client_factory()
        campaign = campaign_factory()
        CampaignEnrollment.objects.create(
            prospective_client=pc,
            campaign=campaign,
            is_active=True,
            next_step_scheduled_at=timezone.now() - timedelta(hours=1),
        )

        upcoming = list(get_upcoming_outreach(hours=48))

        assert len(upcoming) == 0

    def test_excludes_far_future(self, prospective_client_factory, campaign_factory):
        """Excludes enrollments scheduled beyond the hours parameter."""
        pc = prospective_client_factory()
        campaign = campaign_factory()
        CampaignEnrollment.objects.create(
            prospective_client=pc,
            campaign=campaign,
            is_active=True,
            next_step_scheduled_at=timezone.now() + timedelta(hours=72),
        )

        upcoming = list(get_upcoming_outreach(hours=48))

        assert len(upcoming) == 0

    def test_excludes_inactive_enrollments(
        self, prospective_client_factory, campaign_factory
    ):
        """Excludes inactive enrollments."""
        pc = prospective_client_factory()
        campaign = campaign_factory()
        CampaignEnrollment.objects.create(
            prospective_client=pc,
            campaign=campaign,
            is_active=False,
            next_step_scheduled_at=timezone.now() + timedelta(hours=12),
        )

        upcoming = list(get_upcoming_outreach(hours=48))

        assert len(upcoming) == 0


# =============================================================================
# Conversion Funnel Tests
# =============================================================================


@pytest.mark.django_db
class TestGetConversionFunnel:
    """Tests for get_conversion_funnel function."""

    def test_empty_funnel(self):
        """Funnel works with no data."""
        funnel = get_conversion_funnel(days=30)

        assert funnel["new_created"] == 0
        assert funnel["contacted"] == 0
        assert funnel["qualified"] == 0
        assert funnel["proposal"] == 0
        assert funnel["won"] == 0
        assert funnel["lost"] == 0

    def test_counts_created_in_period(self, prospective_client_factory):
        """Counts prospects created within the period."""
        prospective_client_factory(status=ProspectiveClient.Status.NEW)
        prospective_client_factory(status=ProspectiveClient.Status.NEW)

        funnel = get_conversion_funnel(days=30)

        assert funnel["new_created"] == 2

    def test_funnel_progression(self, prospective_client_factory):
        """Funnel shows progression through stages."""
        prospective_client_factory(status=ProspectiveClient.Status.NEW)
        prospective_client_factory(status=ProspectiveClient.Status.CONTACTED)
        prospective_client_factory(status=ProspectiveClient.Status.QUALIFIED)
        prospective_client_factory(status=ProspectiveClient.Status.WON)

        funnel = get_conversion_funnel(days=30)

        assert funnel["new_created"] == 4
        assert funnel["contacted"] == 3  # contacted, qualified, won
        assert funnel["qualified"] == 2  # qualified, won
        assert funnel["won"] == 1


# =============================================================================
# Campaign Performance Tests
# =============================================================================


@pytest.mark.django_db
class TestGetCampaignPerformance:
    """Tests for get_campaign_performance function."""

    def test_empty_without_active_campaigns(self):
        """Returns empty list when no active campaigns."""
        performance = get_campaign_performance()

        assert performance == []

    def test_counts_enrollments(self, prospective_client_factory, campaign_factory):
        """Counts total and active enrollments."""
        campaign = campaign_factory(status=OutreachCampaign.Status.ACTIVE)
        pc1 = prospective_client_factory()
        pc2 = prospective_client_factory()

        CampaignEnrollment.objects.create(
            prospective_client=pc1, campaign=campaign, is_active=True
        )
        CampaignEnrollment.objects.create(
            prospective_client=pc2, campaign=campaign, is_active=False
        )

        performance = get_campaign_performance()

        assert len(performance) == 1
        assert performance[0]["total_enrollments"] == 2
        assert performance[0]["active_enrollments"] == 1

    def test_excludes_inactive_campaigns(self, campaign_factory):
        """Excludes draft, paused, completed, archived campaigns."""
        campaign_factory(status=OutreachCampaign.Status.DRAFT)
        campaign_factory(status=OutreachCampaign.Status.PAUSED)
        campaign_factory(status=OutreachCampaign.Status.COMPLETED)
        campaign_factory(status=OutreachCampaign.Status.ARCHIVED)

        performance = get_campaign_performance()

        assert len(performance) == 0


# =============================================================================
# Activity By Day Tests
# =============================================================================


@pytest.mark.django_db
class TestGetActivityByDay:
    """Tests for get_activity_by_day function."""

    def test_empty_without_touchpoints(self):
        """Returns empty list when no touchpoints."""
        activity = get_activity_by_day(days=30)

        assert activity == []

    def test_groups_by_date(self, prospective_client_factory, touchpoint_factory):
        """Groups touchpoints by date."""
        pc = prospective_client_factory()
        today = timezone.now()
        yesterday = today - timedelta(days=1)

        touchpoint_factory(pc, occurred_at=today)
        touchpoint_factory(pc, occurred_at=today)
        touchpoint_factory(pc, occurred_at=yesterday)

        activity = get_activity_by_day(days=30)

        assert len(activity) == 2

    def test_days_parameter_filters(self, prospective_client_factory, touchpoint_factory):
        """days parameter limits the date range."""
        pc = prospective_client_factory()
        touchpoint_factory(pc, occurred_at=timezone.now() - timedelta(days=60))

        activity = get_activity_by_day(days=30)

        assert len(activity) == 0


# =============================================================================
# Full Dashboard Tests
# =============================================================================


@pytest.mark.django_db
class TestGetFullDashboard:
    """Tests for get_full_dashboard function."""

    def test_returns_all_sections(self):
        """Full dashboard includes all expected sections."""
        dashboard = get_full_dashboard()

        assert "pipeline_summary" in dashboard
        assert "stale_prospects" in dashboard
        assert "unassigned_prospects" in dashboard
        assert "seller_performance" in dashboard
        assert "upcoming_outreach" in dashboard
        assert "conversion_funnel" in dashboard
        assert "campaign_performance" in dashboard
        assert "activity_by_day" in dashboard
        assert "generated_at" in dashboard

    def test_stale_prospects_serialized(self, prospective_client_factory):
        """Stale prospects are serialized to dicts."""
        prospective_client_factory(status=ProspectiveClient.Status.NEW)

        dashboard = get_full_dashboard()

        assert len(dashboard["stale_prospects"]) == 1
        assert "uuid" in dashboard["stale_prospects"][0]
        assert "company_name" in dashboard["stale_prospects"][0]
        assert "days_since_contact" in dashboard["stale_prospects"][0]

    def test_parameters_passed_through(self, prospective_client_factory, touchpoint_factory):
        """stale_days and activity_days parameters are used."""
        pc = prospective_client_factory(status=ProspectiveClient.Status.NEW)
        touchpoint_factory(pc, occurred_at=timezone.now() - timedelta(days=10))

        # With 14-day threshold, not stale
        dashboard = get_full_dashboard(stale_days=14)
        assert len(dashboard["stale_prospects"]) == 0

        # With 7-day threshold, is stale
        dashboard = get_full_dashboard(stale_days=7)
        assert len(dashboard["stale_prospects"]) == 1


# =============================================================================
# Dashboard API Tests
# =============================================================================


@pytest.mark.django_db
class TestDashboardAPI:
    """Tests for Dashboard API endpoints."""

    def test_dashboard_list_authenticated(self, authenticated_client):
        """Authenticated users can access dashboard."""
        response = authenticated_client.get("/api/acquisitions/dashboard/")
        assert response.status_code == 200
        assert "pipeline_summary" in response.data

    def test_dashboard_list_unauthenticated(self, api_client):
        """Unauthenticated users cannot access dashboard."""
        response = api_client.get("/api/acquisitions/dashboard/")
        assert response.status_code in [401, 403]

    def test_dashboard_pipeline_endpoint(self, authenticated_client):
        """Pipeline endpoint returns summary."""
        response = authenticated_client.get("/api/acquisitions/dashboard/pipeline/")
        assert response.status_code == 200
        assert "new" in response.data
        assert "active" in response.data

    def test_dashboard_stale_endpoint(self, authenticated_client, prospective_client_factory):
        """Stale endpoint returns stale prospects."""
        prospective_client_factory(status=ProspectiveClient.Status.NEW)

        response = authenticated_client.get("/api/acquisitions/dashboard/stale/")
        assert response.status_code == 200
        assert len(response.data) == 1

    def test_dashboard_stale_days_param(
        self, authenticated_client, prospective_client_factory, touchpoint_factory
    ):
        """Stale endpoint respects days parameter."""
        pc = prospective_client_factory(status=ProspectiveClient.Status.NEW)
        touchpoint_factory(pc, occurred_at=timezone.now() - timedelta(days=10))

        response = authenticated_client.get("/api/acquisitions/dashboard/stale/?days=7")
        assert response.status_code == 200
        assert len(response.data) == 1

        response = authenticated_client.get("/api/acquisitions/dashboard/stale/?days=14")
        assert response.status_code == 200
        assert len(response.data) == 0

    def test_dashboard_unassigned_endpoint(
        self, authenticated_client, prospective_client_factory
    ):
        """Unassigned endpoint returns unassigned prospects."""
        prospective_client_factory(assigned_to_id=None)

        response = authenticated_client.get("/api/acquisitions/dashboard/unassigned/")
        assert response.status_code == 200
        assert len(response.data) == 1

    def test_dashboard_sellers_endpoint(
        self, authenticated_client, seller_profile_factory, user
    ):
        """Sellers endpoint returns seller performance."""
        seller_profile_factory(user)

        response = authenticated_client.get("/api/acquisitions/dashboard/sellers/")
        assert response.status_code == 200
        assert len(response.data) == 1

    def test_dashboard_funnel_endpoint(self, authenticated_client):
        """Funnel endpoint returns conversion funnel."""
        response = authenticated_client.get("/api/acquisitions/dashboard/funnel/")
        assert response.status_code == 200
        assert "new_created" in response.data
        assert "won" in response.data

    def test_dashboard_campaigns_endpoint(self, authenticated_client):
        """Campaigns endpoint returns campaign performance."""
        response = authenticated_client.get("/api/acquisitions/dashboard/campaigns/")
        assert response.status_code == 200
        assert isinstance(response.data, list)

    def test_dashboard_activity_endpoint(self, authenticated_client):
        """Activity endpoint returns activity by day."""
        response = authenticated_client.get("/api/acquisitions/dashboard/activity/")
        assert response.status_code == 200
        assert isinstance(response.data, list)


# =============================================================================
# Admin Dashboard Tests
# =============================================================================


@pytest.mark.django_db
class TestAdminDashboard:
    """Tests for admin dashboard view."""

    def test_dashboard_requires_login(self, client):
        """Dashboard requires admin login."""
        response = client.get("/admin/acquisitions/dashboard/")
        # Should redirect to login
        assert response.status_code == 302
        assert "login" in response.url

    def test_dashboard_accessible_to_staff(self, client, staff_user):
        """Staff users can access dashboard."""
        client.force_login(staff_user)
        response = client.get("/admin/acquisitions/dashboard/")
        assert response.status_code == 200

    def test_dashboard_template_used(self, client, staff_user):
        """Dashboard uses correct template."""
        client.force_login(staff_user)
        response = client.get("/admin/acquisitions/dashboard/")
        assert "admin/acquisitions/dashboard.html" in [t.name for t in response.templates]

    def test_dashboard_context_has_pipeline(self, client, staff_user):
        """Dashboard context includes pipeline summary."""
        client.force_login(staff_user)
        response = client.get("/admin/acquisitions/dashboard/")
        assert "pipeline" in response.context

    def test_dashboard_context_has_stale_prospects(self, client, staff_user):
        """Dashboard context includes stale prospects."""
        client.force_login(staff_user)
        response = client.get("/admin/acquisitions/dashboard/")
        assert "stale_prospects" in response.context

    def test_dashboard_stale_days_param(
        self, client, staff_user, prospective_client_factory, touchpoint_factory
    ):
        """Dashboard respects stale_days query parameter."""
        pc = prospective_client_factory(status=ProspectiveClient.Status.NEW)
        touchpoint_factory(pc, occurred_at=timezone.now() - timedelta(days=10))

        client.force_login(staff_user)

        response = client.get("/admin/acquisitions/dashboard/?stale_days=7")
        assert len(response.context["stale_prospects"]) == 1

        response = client.get("/admin/acquisitions/dashboard/?stale_days=14")
        assert len(response.context["stale_prospects"]) == 0
