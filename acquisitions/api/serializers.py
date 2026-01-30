"""
DRF serializers for customer acquisition.

Requires: pip install django-acquisitions[drf]
"""

try:
    from rest_framework import serializers

    from ..models import (
        CampaignEnrollment,
        CampaignStep,
        Lead,
        LeadContact,
        MarketingDocument,
        OutreachCampaign,
        SellerProfile,
        Touchpoint,
    )

    class LeadContactSerializer(serializers.ModelSerializer):
        """Serializer for LeadContact."""

        class Meta:
            model = LeadContact
            fields = [
                "uuid",
                "first_name",
                "last_name",
                "title",
                "role",
                "email",
                "phone",
                "phone_mobile",
                "is_primary",
                "preferred_contact_method",
                "best_time_to_contact",
                "opted_out_email",
                "opted_out_sms",
                "opted_out_phone",
                "notes",
                "created_at",
                "updated_at",
            ]
            read_only_fields = ["uuid", "created_at", "updated_at"]

    class TouchpointSerializer(serializers.ModelSerializer):
        """Serializer for Touchpoint."""

        contact_uuid = serializers.SlugRelatedField(
            source="contact",
            slug_field="uuid",
            queryset=LeadContact.objects.all(),
            required=False,
            allow_null=True,
        )

        class Meta:
            model = Touchpoint
            fields = [
                "uuid",
                "touchpoint_type",
                "direction",
                "outcome",
                "contact_uuid",
                "subject",
                "notes",
                "occurred_at",
                "duration_minutes",
                "performed_by_id",
                "is_automated",
                "external_id",
                "created_at",
                "updated_at",
            ]
            read_only_fields = ["uuid", "created_at", "updated_at", "is_automated", "external_id"]

    class LeadListSerializer(serializers.ModelSerializer):
        """Serializer for Lead list view."""

        contact_count = serializers.IntegerField(source="contacts.count", read_only=True)
        touchpoint_count = serializers.IntegerField(source="touchpoints.count", read_only=True)

        class Meta:
            model = Lead
            fields = [
                "uuid",
                "company_name",
                "industry",
                "status",
                "source",
                "email",
                "phone",
                "city",
                "state",
                "score",
                "priority",
                "estimated_value",
                "assigned_to_id",
                "contact_count",
                "touchpoint_count",
                "created_at",
                "updated_at",
            ]
            read_only_fields = ["uuid", "created_at", "updated_at"]

    class LeadDetailSerializer(serializers.ModelSerializer):
        """Serializer for Lead detail view."""

        contacts = LeadContactSerializer(many=True, read_only=True)
        recent_touchpoints = serializers.SerializerMethodField()

        class Meta:
            model = Lead
            fields = [
                "uuid",
                "company_name",
                "industry",
                "website",
                "status",
                "source",
                "email",
                "phone",
                "address_line1",
                "address_line2",
                "city",
                "state",
                "postal_code",
                "country",
                "score",
                "priority",
                "estimated_value",
                "notes",
                "assigned_to_id",
                "converted_at",
                "converted_to_id",
                "contacts",
                "recent_touchpoints",
                "created_at",
                "updated_at",
            ]
            read_only_fields = ["uuid", "created_at", "updated_at", "converted_at", "converted_to_id"]

        def get_recent_touchpoints(self, obj):
            touchpoints = obj.touchpoints.all()[:10]
            return TouchpointSerializer(touchpoints, many=True).data

    class LeadCreateSerializer(serializers.ModelSerializer):
        """Serializer for creating a Lead."""

        class Meta:
            model = Lead
            fields = [
                "company_name",
                "industry",
                "website",
                "status",
                "source",
                "email",
                "phone",
                "address_line1",
                "address_line2",
                "city",
                "state",
                "postal_code",
                "country",
                "score",
                "priority",
                "estimated_value",
                "notes",
                "assigned_to_id",
            ]

    class CampaignStepSerializer(serializers.ModelSerializer):
        """Serializer for CampaignStep."""

        class Meta:
            model = CampaignStep
            fields = [
                "id",
                "step_order",
                "step_type",
                "delay_days",
                "delay_hours",
                "subject_template",
                "body_template",
                "skip_if_responded",
                "is_active",
            ]

    class OutreachCampaignSerializer(serializers.ModelSerializer):
        """Serializer for OutreachCampaign."""

        steps = CampaignStepSerializer(many=True, read_only=True)
        enrollment_count = serializers.IntegerField(source="enrollments.count", read_only=True)

        class Meta:
            model = OutreachCampaign
            fields = [
                "uuid",
                "name",
                "description",
                "status",
                "start_date",
                "end_date",
                "max_contacts_per_day",
                "created_by_id",
                "steps",
                "enrollment_count",
                "created_at",
                "updated_at",
            ]
            read_only_fields = ["uuid", "created_at", "updated_at"]

    class CampaignEnrollmentSerializer(serializers.ModelSerializer):
        """Serializer for CampaignEnrollment."""

        lead_uuid = serializers.SlugRelatedField(
            source="lead",
            slug_field="uuid",
            read_only=True,
        )
        campaign_uuid = serializers.SlugRelatedField(
            source="campaign",
            slug_field="uuid",
            read_only=True,
        )

        class Meta:
            model = CampaignEnrollment
            fields = [
                "id",
                "lead_uuid",
                "campaign_uuid",
                "current_step",
                "next_step_scheduled_at",
                "is_active",
                "completed_at",
                "enrolled_at",
            ]
            read_only_fields = ["id", "enrolled_at", "completed_at"]

    class MarketingDocumentSerializer(serializers.ModelSerializer):
        """Serializer for MarketingDocument."""

        class Meta:
            model = MarketingDocument
            fields = [
                "uuid",
                "name",
                "document_type",
                "description",
                "file",
                "external_url",
                "version",
                "is_internal_only",
                "is_active",
                "view_count",
                "download_count",
                "created_at",
                "updated_at",
            ]
            read_only_fields = ["uuid", "view_count", "download_count", "created_at", "updated_at"]

    class SellerProfileSerializer(serializers.ModelSerializer):
        """Serializer for SellerProfile."""

        class Meta:
            model = SellerProfile
            fields = [
                "uuid",
                "user_id",
                "display_name",
                "email",
                "phone",
                "email_signature",
                "auto_assign_leads",
                "max_active_leads",
                "working_hours_start",
                "working_hours_end",
                "working_days",
                "timezone",
                "total_leads_converted",
                "active_leads_count",
                "is_active",
                "created_at",
                "updated_at",
            ]
            read_only_fields = [
                "uuid",
                "total_leads_converted",
                "active_leads_count",
                "created_at",
                "updated_at",
            ]

except ImportError:
    # DRF not installed
    pass
