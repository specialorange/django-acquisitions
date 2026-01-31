"""
Dashboard service for team overview and analytics.

Provides aggregated data about prospective clients, stale contacts,
seller performance, and pipeline health.
"""

from datetime import timedelta
from django.db.models import Count, Q, Max, Avg
from django.db.models.functions import TruncDate
from django.utils import timezone

from ..models import (
    CampaignEnrollment,
    OutreachCampaign,
    ProspectiveClient,
    SellerProfile,
    Touchpoint,
)


def get_pipeline_summary():
    """
    Get counts of prospective clients by status.

    Returns:
        dict: Status counts and totals
    """
    counts = (
        ProspectiveClient.objects
        .values("status")
        .annotate(count=Count("id"))
        .order_by("status")
    )

    summary = {item["status"]: item["count"] for item in counts}

    # Ensure all statuses are present
    for status_choice in ProspectiveClient.Status.choices:
        if status_choice[0] not in summary:
            summary[status_choice[0]] = 0

    # Add computed totals
    active_statuses = ["new", "contacted", "qualified", "proposal", "negotiation"]
    summary["_total"] = sum(summary.values())
    summary["_active"] = sum(summary.get(s, 0) for s in active_statuses)
    summary["_closed"] = summary.get("won", 0) + summary.get("lost", 0)

    return summary


def get_stale_prospects(days=14, limit=50):
    """
    Get prospective clients with no recent touchpoints.

    Args:
        days: Number of days without contact to be considered stale
        limit: Maximum number of results

    Returns:
        QuerySet: Stale prospective clients with last touchpoint info
    """
    cutoff = timezone.now() - timedelta(days=days)

    # Active prospects only
    active_statuses = [
        ProspectiveClient.Status.NEW,
        ProspectiveClient.Status.CONTACTED,
        ProspectiveClient.Status.QUALIFIED,
        ProspectiveClient.Status.PROPOSAL,
        ProspectiveClient.Status.NEGOTIATION,
    ]

    stale = (
        ProspectiveClient.objects
        .filter(status__in=active_statuses)
        .annotate(
            last_touchpoint=Max("touchpoints__occurred_at"),
            touchpoint_count=Count("touchpoints"),
        )
        .filter(
            Q(last_touchpoint__lt=cutoff) | Q(last_touchpoint__isnull=True)
        )
        .order_by("last_touchpoint", "-priority", "-score")[:limit]
    )

    return stale


def get_unassigned_prospects(limit=50):
    """
    Get prospective clients not assigned to any seller.

    Args:
        limit: Maximum number of results

    Returns:
        QuerySet: Unassigned prospective clients
    """
    active_statuses = [
        ProspectiveClient.Status.NEW,
        ProspectiveClient.Status.CONTACTED,
        ProspectiveClient.Status.QUALIFIED,
        ProspectiveClient.Status.PROPOSAL,
        ProspectiveClient.Status.NEGOTIATION,
    ]

    return (
        ProspectiveClient.objects
        .filter(status__in=active_statuses, assigned_to_id__isnull=True)
        .order_by("priority", "-score", "-created_at")[:limit]
    )


def get_seller_performance(days=30):
    """
    Get seller performance metrics.

    Args:
        days: Number of days to look back

    Returns:
        list: Seller stats sorted by conversions
    """
    cutoff = timezone.now() - timedelta(days=days)

    # Get all active sellers
    sellers = SellerProfile.objects.filter(is_active=True)

    performance = []
    for seller in sellers:
        # Count conversions in period
        conversions = ProspectiveClient.objects.filter(
            assigned_to_id=seller.user_id,
            status=ProspectiveClient.Status.WON,
            converted_at__gte=cutoff,
        ).count()

        # Count active prospects
        active = ProspectiveClient.objects.filter(
            assigned_to_id=seller.user_id,
            status__in=[
                ProspectiveClient.Status.NEW,
                ProspectiveClient.Status.CONTACTED,
                ProspectiveClient.Status.QUALIFIED,
                ProspectiveClient.Status.PROPOSAL,
                ProspectiveClient.Status.NEGOTIATION,
            ],
        ).count()

        # Count touchpoints in period
        touchpoints = Touchpoint.objects.filter(
            performed_by_id=seller.user_id,
            occurred_at__gte=cutoff,
        ).count()

        performance.append({
            "seller_id": seller.user_id,
            "display_name": seller.display_name,
            "email": seller.email,
            "conversions": conversions,
            "active_prospects": active,
            "touchpoints": touchpoints,
        })

    # Sort by conversions descending
    performance.sort(key=lambda x: (-x["conversions"], -x["touchpoints"]))

    return performance


def get_upcoming_outreach(hours=48, limit=50):
    """
    Get scheduled campaign outreach coming up.

    Args:
        hours: Hours to look ahead
        limit: Maximum number of results

    Returns:
        QuerySet: Upcoming enrollments with next step scheduled
    """
    now = timezone.now()
    cutoff = now + timedelta(hours=hours)

    return (
        CampaignEnrollment.objects
        .filter(
            is_active=True,
            next_step_scheduled_at__gte=now,
            next_step_scheduled_at__lte=cutoff,
        )
        .select_related("prospective_client", "campaign")
        .order_by("next_step_scheduled_at")[:limit]
    )


def get_recent_activity(days=7, limit=100):
    """
    Get recent touchpoint activity across the team.

    Args:
        days: Number of days to look back
        limit: Maximum number of results

    Returns:
        QuerySet: Recent touchpoints
    """
    cutoff = timezone.now() - timedelta(days=days)

    return (
        Touchpoint.objects
        .filter(occurred_at__gte=cutoff)
        .select_related("prospective_client", "contact")
        .order_by("-occurred_at")[:limit]
    )


def get_activity_by_day(days=30):
    """
    Get touchpoint counts by day for charting.

    Args:
        days: Number of days to look back

    Returns:
        list: Daily activity counts
    """
    cutoff = timezone.now() - timedelta(days=days)

    daily = (
        Touchpoint.objects
        .filter(occurred_at__gte=cutoff)
        .annotate(date=TruncDate("occurred_at"))
        .values("date")
        .annotate(count=Count("id"))
        .order_by("date")
    )

    return list(daily)


def get_conversion_funnel(days=30):
    """
    Get conversion funnel metrics.

    Args:
        days: Number of days to look back for new prospects

    Returns:
        dict: Funnel stage counts
    """
    cutoff = timezone.now() - timedelta(days=days)

    # Prospects created in the period
    created = ProspectiveClient.objects.filter(created_at__gte=cutoff)

    funnel = {
        "new_created": created.count(),
        "contacted": created.filter(
            status__in=[
                ProspectiveClient.Status.CONTACTED,
                ProspectiveClient.Status.QUALIFIED,
                ProspectiveClient.Status.PROPOSAL,
                ProspectiveClient.Status.NEGOTIATION,
                ProspectiveClient.Status.WON,
            ]
        ).count(),
        "qualified": created.filter(
            status__in=[
                ProspectiveClient.Status.QUALIFIED,
                ProspectiveClient.Status.PROPOSAL,
                ProspectiveClient.Status.NEGOTIATION,
                ProspectiveClient.Status.WON,
            ]
        ).count(),
        "proposal": created.filter(
            status__in=[
                ProspectiveClient.Status.PROPOSAL,
                ProspectiveClient.Status.NEGOTIATION,
                ProspectiveClient.Status.WON,
            ]
        ).count(),
        "won": created.filter(status=ProspectiveClient.Status.WON).count(),
        "lost": created.filter(status=ProspectiveClient.Status.LOST).count(),
    }

    return funnel


def get_campaign_performance():
    """
    Get performance metrics for active campaigns.

    Returns:
        list: Campaign stats
    """
    campaigns = OutreachCampaign.objects.filter(
        status=OutreachCampaign.Status.ACTIVE
    )

    performance = []
    for campaign in campaigns:
        enrollments = campaign.enrollments.all()
        total = enrollments.count()
        active = enrollments.filter(is_active=True).count()
        completed = enrollments.filter(is_active=False, completed_at__isnull=False).count()

        # Count responses (inbound touchpoints from enrolled prospects)
        enrolled_prospect_ids = enrollments.values_list("prospective_client_id", flat=True)
        responses = Touchpoint.objects.filter(
            prospective_client_id__in=enrolled_prospect_ids,
            direction=Touchpoint.Direction.INBOUND,
            campaign=campaign,
        ).count()

        performance.append({
            "campaign_id": campaign.id,
            "uuid": str(campaign.uuid),
            "name": campaign.name,
            "total_enrollments": total,
            "active_enrollments": active,
            "completed_enrollments": completed,
            "responses": responses,
            "response_rate": (responses / total * 100) if total > 0 else 0,
        })

    return performance


def get_full_dashboard(stale_days=14, activity_days=30):
    """
    Get complete dashboard data.

    Args:
        stale_days: Days without contact to be considered stale
        activity_days: Days to look back for activity metrics

    Returns:
        dict: Complete dashboard data
    """
    return {
        "pipeline_summary": get_pipeline_summary(),
        "stale_prospects": [
            {
                "id": p.id,
                "uuid": str(p.uuid),
                "company_name": p.company_name,
                "status": p.status,
                "priority": p.priority,
                "score": p.score,
                "assigned_to_id": p.assigned_to_id,
                "last_touchpoint": p.last_touchpoint,
                "touchpoint_count": p.touchpoint_count,
                "days_since_contact": (
                    (timezone.now() - p.last_touchpoint).days
                    if p.last_touchpoint else None
                ),
            }
            for p in get_stale_prospects(days=stale_days)
        ],
        "unassigned_prospects": [
            {
                "id": p.id,
                "uuid": str(p.uuid),
                "company_name": p.company_name,
                "status": p.status,
                "priority": p.priority,
                "score": p.score,
                "created_at": p.created_at,
            }
            for p in get_unassigned_prospects()
        ],
        "seller_performance": get_seller_performance(days=activity_days),
        "upcoming_outreach": [
            {
                "enrollment_id": e.id,
                "prospective_client": {
                    "uuid": str(e.prospective_client.uuid),
                    "company_name": e.prospective_client.company_name,
                },
                "campaign": {
                    "uuid": str(e.campaign.uuid),
                    "name": e.campaign.name,
                },
                "current_step": e.current_step,
                "next_step_scheduled_at": e.next_step_scheduled_at,
            }
            for e in get_upcoming_outreach()
        ],
        "conversion_funnel": get_conversion_funnel(days=activity_days),
        "campaign_performance": get_campaign_performance(),
        "activity_by_day": get_activity_by_day(days=activity_days),
        "generated_at": timezone.now(),
    }
