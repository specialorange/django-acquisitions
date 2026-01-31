"""
Django admin configuration for customer acquisition models.
"""

from django.contrib import admin
from django.template.response import TemplateResponse
from django.urls import path
from django.utils import timezone
from django.utils.html import format_html

from .models import (
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


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin for Category model."""

    list_display = ["name", "color", "is_active", "prospective_client_count"]
    list_filter = ["is_active"]
    search_fields = ["name", "description"]

    @admin.display(description="Prospective Clients")
    def prospective_client_count(self, obj):
        return obj.prospective_clients.count()


@admin.register(Industry)
class IndustryAdmin(admin.ModelAdmin):
    """Admin for Industry model."""

    list_display = ["name", "is_active", "prospective_client_count"]
    list_filter = ["is_active"]
    search_fields = ["name", "description"]

    @admin.display(description="Prospective Clients")
    def prospective_client_count(self, obj):
        return obj.prospective_clients.count()


class ProspectiveClientContactInline(admin.TabularInline):
    """Inline for ProspectiveClientContact within ProspectiveClient admin."""

    model = ProspectiveClientContact
    extra = 1
    fields = [
        "first_name",
        "last_name",
        "title",
        "role",
        "email",
        "phone",
        "is_primary",
    ]


class TouchpointInline(admin.TabularInline):
    """Inline for recent Touchpoints within ProspectiveClient admin."""

    model = Touchpoint
    extra = 0
    max_num = 5
    fk_name = "prospective_client"
    fields = [
        "touchpoint_type",
        "direction",
        "outcome",
        "subject",
        "occurred_at",
        "is_automated",
    ]
    readonly_fields = ["is_automated"]
    ordering = ["-occurred_at"]

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(ProspectiveClient)
class ProspectiveClientAdmin(admin.ModelAdmin):
    """Admin for ProspectiveClient model."""

    list_display = [
        "company_name",
        "status_badge",
        "source",
        "industry",
        "city",
        "state",
        "score",
        "priority",
        "contact_count",
        "created_at",
    ]
    list_filter = [
        "status",
        "source",
        "industry",
        "categories",
        "priority",
        "state",
        "created_at",
    ]
    filter_horizontal = ["categories"]
    search_fields = [
        "company_name",
        "city",
        "contacts__first_name",
        "contacts__last_name",
        "contacts__email",
    ]
    readonly_fields = [
        "uuid",
        "created_at",
        "updated_at",
        "converted_at",
    ]
    list_editable = ["priority"]
    date_hierarchy = "created_at"
    inlines = [ProspectiveClientContactInline, TouchpointInline]

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "company_name",
                    "industry",
                    "categories",
                    "website",
                )
            },
        ),
        (
            "Status",
            {
                "fields": (
                    "status",
                    "source",
                    "score",
                    "priority",
                    "estimated_value",
                )
            },
        ),
        (
            "Address",
            {
                "fields": (
                    "address_line1",
                    "address_line2",
                    "city",
                    "state",
                    "postal_code",
                    "country",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Assignment",
            {
                "fields": (
                    "assigned_to_id",
                    "notes",
                )
            },
        ),
        (
            "Conversion",
            {
                "fields": (
                    "converted_at",
                    "converted_to_id",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Metadata",
            {
                "fields": (
                    "uuid",
                    "is_sample",
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    actions = ["mark_as_contacted", "mark_as_qualified", "mark_as_lost"]

    @admin.display(description="Status")
    def status_badge(self, obj):
        colors = {
            "new": "#3498db",
            "contacted": "#9b59b6",
            "qualified": "#f39c12",
            "proposal": "#e67e22",
            "negotiation": "#e74c3c",
            "won": "#27ae60",
            "lost": "#95a5a6",
            "dormant": "#7f8c8d",
        }
        color = colors.get(obj.status, "#333")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display(),
        )

    @admin.display(description="Contacts")
    def contact_count(self, obj):
        return obj.contacts.count()

    @admin.action(description="Mark selected as Contacted")
    def mark_as_contacted(self, request, queryset):
        queryset.update(status=ProspectiveClient.Status.CONTACTED)

    @admin.action(description="Mark selected as Qualified")
    def mark_as_qualified(self, request, queryset):
        queryset.update(status=ProspectiveClient.Status.QUALIFIED)

    @admin.action(description="Mark selected as Lost")
    def mark_as_lost(self, request, queryset):
        queryset.update(status=ProspectiveClient.Status.LOST)


@admin.register(ProspectiveClientContact)
class ProspectiveClientContactAdmin(admin.ModelAdmin):
    """Admin for ProspectiveClientContact model."""

    list_display = [
        "full_name",
        "prospective_client",
        "title",
        "role",
        "email",
        "phone",
        "is_primary",
    ]
    list_filter = [
        "role",
        "is_primary",
        "preferred_contact_method",
        "opted_out_email",
        "opted_out_sms",
    ]
    search_fields = [
        "first_name",
        "last_name",
        "email",
        "prospective_client__company_name",
    ]
    raw_id_fields = ["prospective_client"]
    readonly_fields = ["uuid", "created_at", "updated_at"]


@admin.register(Touchpoint)
class TouchpointAdmin(admin.ModelAdmin):
    """Admin for Touchpoint model."""

    list_display = [
        "prospective_client",
        "touchpoint_type",
        "direction",
        "outcome",
        "subject",
        "occurred_at",
        "is_automated",
    ]
    list_filter = [
        "touchpoint_type",
        "direction",
        "outcome",
        "is_automated",
        "occurred_at",
    ]
    search_fields = [
        "prospective_client__company_name",
        "subject",
        "notes",
    ]
    raw_id_fields = ["prospective_client", "contact", "campaign"]
    readonly_fields = ["uuid", "created_at", "updated_at"]
    date_hierarchy = "occurred_at"


class CampaignStepInline(admin.TabularInline):
    """Inline for CampaignStep within OutreachCampaign admin."""

    model = CampaignStep
    extra = 1
    fields = [
        "step_order",
        "step_type",
        "delay_days",
        "delay_hours",
        "subject_template",
        "skip_if_responded",
        "is_active",
    ]


@admin.register(OutreachCampaign)
class OutreachCampaignAdmin(admin.ModelAdmin):
    """Admin for OutreachCampaign model."""

    list_display = [
        "name",
        "status",
        "start_date",
        "end_date",
        "step_count",
        "enrollment_count",
        "created_at",
    ]
    list_filter = [
        "status",
        "start_date",
        "created_at",
    ]
    search_fields = ["name", "description"]
    readonly_fields = ["uuid", "created_at", "updated_at"]
    inlines = [CampaignStepInline]

    @admin.display(description="Steps")
    def step_count(self, obj):
        return obj.steps.count()

    @admin.display(description="Enrollments")
    def enrollment_count(self, obj):
        return obj.enrollments.count()


@admin.register(CampaignEnrollment)
class CampaignEnrollmentAdmin(admin.ModelAdmin):
    """Admin for CampaignEnrollment model."""

    list_display = [
        "prospective_client",
        "campaign",
        "current_step",
        "next_step_scheduled_at",
        "is_active",
        "enrolled_at",
    ]
    list_filter = [
        "is_active",
        "campaign",
        "enrolled_at",
    ]
    search_fields = [
        "prospective_client__company_name",
        "campaign__name",
    ]
    raw_id_fields = ["prospective_client", "campaign"]
    readonly_fields = ["enrolled_at", "updated_at"]


@admin.register(MarketingDocument)
class MarketingDocumentAdmin(admin.ModelAdmin):
    """Admin for MarketingDocument model."""

    list_display = [
        "name",
        "document_type",
        "version",
        "is_internal_only",
        "is_active",
        "view_count",
        "download_count",
        "created_at",
    ]
    list_filter = [
        "document_type",
        "is_internal_only",
        "is_active",
        "created_at",
    ]
    search_fields = ["name", "description"]
    readonly_fields = [
        "uuid",
        "view_count",
        "download_count",
        "created_at",
        "updated_at",
    ]


@admin.register(SellerProfile)
class SellerProfileAdmin(admin.ModelAdmin):
    """Admin for SellerProfile model."""

    list_display = [
        "display_name",
        "email",
        "user_id",
        "auto_assign_prospective_clients",
        "active_prospective_clients_count",
        "total_converted",
        "is_active",
    ]
    list_filter = [
        "is_active",
        "auto_assign_prospective_clients",
        "timezone",
    ]
    search_fields = ["display_name", "email"]
    readonly_fields = [
        "uuid",
        "total_converted",
        "active_prospective_clients_count",
        "created_at",
        "updated_at",
    ]


class AcquisitionsAdminSite(admin.AdminSite):
    """Custom admin site with dashboard."""

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "acquisitions/dashboard/",
                self.admin_view(self.dashboard_view),
                name="acquisitions_dashboard",
            ),
        ]
        return custom_urls + urls

    def dashboard_view(self, request):
        """Team dashboard view."""
        from .services.dashboard import (
            get_campaign_performance,
            get_conversion_funnel,
            get_pipeline_summary,
            get_seller_performance,
            get_stale_prospects,
            get_unassigned_prospects,
            get_upcoming_outreach,
        )

        stale_days = int(request.GET.get("stale_days", 14))
        activity_days = int(request.GET.get("activity_days", 30))

        # Get stale prospects with annotated data
        stale_qs = get_stale_prospects(days=stale_days, limit=20)
        stale_prospects = []
        for pc in stale_qs:
            pc.days_since_contact = (
                (timezone.now() - pc.last_touchpoint).days
                if pc.last_touchpoint else None
            )
            stale_prospects.append(pc)

        context = {
            **self.each_context(request),
            "title": "Acquisitions Dashboard",
            "pipeline": get_pipeline_summary(),
            "stale_prospects": stale_prospects,
            "unassigned_prospects": get_unassigned_prospects(limit=20),
            "seller_performance": get_seller_performance(days=activity_days),
            "upcoming_outreach": get_upcoming_outreach(limit=20),
            "funnel": get_conversion_funnel(days=activity_days),
            "campaign_performance": get_campaign_performance(),
            "stale_days": stale_days,
            "activity_days": activity_days,
            "generated_at": timezone.now(),
        }

        return TemplateResponse(
            request,
            "admin/acquisitions/dashboard.html",
            context,
        )


# Add dashboard URL to the default admin site
def get_admin_urls(urls):
    """Add dashboard URL to admin."""
    from django.urls import path

    def dashboard_view(request):
        """Team dashboard view."""
        from .services.dashboard import (
            get_campaign_performance,
            get_conversion_funnel,
            get_pipeline_summary,
            get_seller_performance,
            get_stale_prospects,
            get_unassigned_prospects,
            get_upcoming_outreach,
        )

        stale_days = int(request.GET.get("stale_days", 14))
        activity_days = int(request.GET.get("activity_days", 30))

        # Get stale prospects with annotated data
        stale_qs = get_stale_prospects(days=stale_days, limit=20)
        stale_prospects = []
        for pc in stale_qs:
            pc.days_since_contact = (
                (timezone.now() - pc.last_touchpoint).days
                if pc.last_touchpoint else None
            )
            stale_prospects.append(pc)

        context = {
            **admin.site.each_context(request),
            "title": "Acquisitions Dashboard",
            "pipeline": get_pipeline_summary(),
            "stale_prospects": stale_prospects,
            "unassigned_prospects": get_unassigned_prospects(limit=20),
            "seller_performance": get_seller_performance(days=activity_days),
            "upcoming_outreach": get_upcoming_outreach(limit=20),
            "funnel": get_conversion_funnel(days=activity_days),
            "campaign_performance": get_campaign_performance(),
            "stale_days": stale_days,
            "activity_days": activity_days,
            "generated_at": timezone.now(),
        }

        return TemplateResponse(
            request,
            "admin/acquisitions/dashboard.html",
            context,
        )

    custom_urls = [
        path(
            "acquisitions/dashboard/",
            admin.site.admin_view(dashboard_view),
            name="acquisitions_dashboard",
        ),
    ]
    return custom_urls + urls


# Monkey-patch admin.site.get_urls to include dashboard
_original_get_urls = admin.site.get_urls


def _patched_get_urls():
    return get_admin_urls(_original_get_urls())


admin.site.get_urls = _patched_get_urls
