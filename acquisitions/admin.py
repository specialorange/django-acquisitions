"""
Django admin configuration for customer acquisition models.
"""

from django.contrib import admin
from django.utils.html import format_html

from .models import (
    CampaignEnrollment,
    CampaignStep,
    Lead,
    LeadContact,
    MarketingDocument,
    OutreachCampaign,
    SellerProfile,
    Touchpoint,
)


class LeadContactInline(admin.TabularInline):
    """Inline for LeadContact within Lead admin."""

    model = LeadContact
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
    """Inline for recent Touchpoints within Lead admin."""

    model = Touchpoint
    extra = 0
    max_num = 5
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


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    """Admin for Lead model."""

    list_display = [
        "company_name",
        "status_badge",
        "source",
        "email",
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
        "priority",
        "state",
        "created_at",
    ]
    search_fields = [
        "company_name",
        "email",
        "phone",
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
    inlines = [LeadContactInline, TouchpointInline]

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "company_name",
                    "industry",
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
            "Contact",
            {
                "fields": (
                    "email",
                    "phone",
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

    @admin.action(description="Mark selected leads as Contacted")
    def mark_as_contacted(self, request, queryset):
        queryset.update(status=Lead.Status.CONTACTED)

    @admin.action(description="Mark selected leads as Qualified")
    def mark_as_qualified(self, request, queryset):
        queryset.update(status=Lead.Status.QUALIFIED)

    @admin.action(description="Mark selected leads as Lost")
    def mark_as_lost(self, request, queryset):
        queryset.update(status=Lead.Status.LOST)


@admin.register(LeadContact)
class LeadContactAdmin(admin.ModelAdmin):
    """Admin for LeadContact model."""

    list_display = [
        "full_name",
        "lead",
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
        "lead__company_name",
    ]
    raw_id_fields = ["lead"]
    readonly_fields = ["uuid", "created_at", "updated_at"]


@admin.register(Touchpoint)
class TouchpointAdmin(admin.ModelAdmin):
    """Admin for Touchpoint model."""

    list_display = [
        "lead",
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
        "lead__company_name",
        "subject",
        "notes",
    ]
    raw_id_fields = ["lead", "contact", "campaign"]
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
        "lead",
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
        "lead__company_name",
        "campaign__name",
    ]
    raw_id_fields = ["lead", "campaign"]
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
        "auto_assign_leads",
        "active_leads_count",
        "total_leads_converted",
        "is_active",
    ]
    list_filter = [
        "is_active",
        "auto_assign_leads",
        "timezone",
    ]
    search_fields = ["display_name", "email"]
    readonly_fields = [
        "uuid",
        "total_leads_converted",
        "active_leads_count",
        "created_at",
        "updated_at",
    ]
