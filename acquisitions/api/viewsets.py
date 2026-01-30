"""
DRF ViewSets for customer acquisition.

Requires: pip install django-acquisitions[drf]
"""

try:
    from rest_framework import status, viewsets
    from rest_framework.decorators import action
    from rest_framework.permissions import IsAuthenticated
    from rest_framework.response import Response

    from ..models import (
        Lead,
        LeadContact,
        MarketingDocument,
        OutreachCampaign,
        SellerProfile,
        Touchpoint,
    )
    from .permissions import HasLeadPermission, IsSellerOrAdmin, ReadOnlyOrAdmin
    from .serializers import (
        LeadContactSerializer,
        LeadCreateSerializer,
        LeadDetailSerializer,
        LeadListSerializer,
        MarketingDocumentSerializer,
        OutreachCampaignSerializer,
        SellerProfileSerializer,
        TouchpointSerializer,
    )

    class UUIDLookupMixin:
        """Use UUID as lookup field."""

        lookup_field = "uuid"
        lookup_url_kwarg = "uuid"

    class MultiSerializerMixin:
        """Use different serializers per action."""

        serializer_classes = {}

        def get_serializer_class(self):
            return self.serializer_classes.get(self.action, self.serializer_class)

    class LeadViewSet(UUIDLookupMixin, MultiSerializerMixin, viewsets.ModelViewSet):
        """
        ViewSet for Lead CRUD operations.

        list: List all leads (with filtering)
        retrieve: Get lead details
        create: Create new lead
        update: Update lead
        destroy: Delete lead
        """

        permission_classes = [IsAuthenticated, HasLeadPermission]
        serializer_class = LeadListSerializer
        serializer_classes = {
            "list": LeadListSerializer,
            "retrieve": LeadDetailSerializer,
            "create": LeadCreateSerializer,
            "update": LeadDetailSerializer,
            "partial_update": LeadDetailSerializer,
        }

        def get_queryset(self):
            """Filter queryset based on query params."""
            qs = Lead.objects.all()

            # Filter by status
            status_filter = self.request.query_params.get("status")
            if status_filter:
                qs = qs.filter(status=status_filter)

            # Filter by assigned user
            assigned_to = self.request.query_params.get("assigned_to")
            if assigned_to == "me":
                qs = qs.filter(assigned_to_id=self.request.user.id)
            elif assigned_to:
                qs = qs.filter(assigned_to_id=assigned_to)

            # Filter by source
            source = self.request.query_params.get("source")
            if source:
                qs = qs.filter(source=source)

            # Search
            search = self.request.query_params.get("search")
            if search:
                qs = qs.filter(company_name__icontains=search)

            return qs.prefetch_related("contacts", "touchpoints")

        @action(detail=True, methods=["post"])
        def convert(self, request, uuid=None):
            """Convert a lead to a customer."""
            lead = self.get_object()

            from ..services.onboarding import convert_lead

            result = convert_lead(lead, request.user)

            if result["success"]:
                return Response(
                    {
                        "success": True,
                        "lead_uuid": str(lead.uuid),
                        "customer_id": result.get("customer_id"),
                    }
                )
            else:
                return Response({"error": result.get("error")}, status=status.HTTP_400_BAD_REQUEST)

        @action(detail=True, methods=["post"])
        def enroll_campaign(self, request, uuid=None):
            """Enroll lead in an outreach campaign."""
            lead = self.get_object()
            campaign_uuid = request.data.get("campaign_uuid")

            if not campaign_uuid:
                return Response(
                    {"error": "campaign_uuid required"}, status=status.HTTP_400_BAD_REQUEST
                )

            try:
                campaign = OutreachCampaign.objects.get(uuid=campaign_uuid)
            except OutreachCampaign.DoesNotExist:
                return Response({"error": "Campaign not found"}, status=status.HTTP_404_NOT_FOUND)

            from ..services.outreach import enroll_lead_in_campaign

            try:
                enrollment = enroll_lead_in_campaign(lead, campaign)
                return Response(
                    {
                        "success": True,
                        "enrollment_id": enrollment.id,
                    }
                )
            except ValueError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    class LeadContactViewSet(UUIDLookupMixin, viewsets.ModelViewSet):
        """ViewSet for LeadContact CRUD."""

        permission_classes = [IsAuthenticated]
        serializer_class = LeadContactSerializer

        def get_queryset(self):
            lead_uuid = self.kwargs.get("lead_uuid")
            if lead_uuid:
                return LeadContact.objects.filter(lead__uuid=lead_uuid)
            return LeadContact.objects.none()

        def perform_create(self, serializer):
            lead_uuid = self.kwargs.get("lead_uuid")
            lead = Lead.objects.get(uuid=lead_uuid)
            serializer.save(lead=lead)

    class TouchpointViewSet(UUIDLookupMixin, viewsets.ModelViewSet):
        """ViewSet for Touchpoint CRUD."""

        permission_classes = [IsAuthenticated]
        serializer_class = TouchpointSerializer

        def get_queryset(self):
            lead_uuid = self.kwargs.get("lead_uuid")
            if lead_uuid:
                return Touchpoint.objects.filter(lead__uuid=lead_uuid)
            return Touchpoint.objects.all()

        def perform_create(self, serializer):
            lead_uuid = self.kwargs.get("lead_uuid")
            if lead_uuid:
                lead = Lead.objects.get(uuid=lead_uuid)
                serializer.save(
                    lead=lead,
                    performed_by_id=self.request.user.id,
                )
            else:
                serializer.save(performed_by_id=self.request.user.id)

    class OutreachCampaignViewSet(UUIDLookupMixin, viewsets.ModelViewSet):
        """ViewSet for OutreachCampaign CRUD."""

        permission_classes = [IsAuthenticated, IsSellerOrAdmin]
        serializer_class = OutreachCampaignSerializer
        queryset = OutreachCampaign.objects.prefetch_related("steps")

        def perform_create(self, serializer):
            serializer.save(created_by_id=self.request.user.id)

    class MarketingDocumentViewSet(UUIDLookupMixin, viewsets.ModelViewSet):
        """ViewSet for MarketingDocument CRUD."""

        permission_classes = [IsAuthenticated, ReadOnlyOrAdmin]
        serializer_class = MarketingDocumentSerializer

        def get_queryset(self):
            qs = MarketingDocument.objects.filter(is_active=True)

            # Filter by document type
            doc_type = self.request.query_params.get("type")
            if doc_type:
                qs = qs.filter(document_type=doc_type)

            # Non-internal documents for non-staff
            if not self.request.user.is_staff:
                qs = qs.filter(is_internal_only=False)

            return qs

        @action(detail=True, methods=["post"])
        def track_view(self, request, uuid=None):
            """Track document view."""
            doc = self.get_object()
            doc.increment_view_count()
            return Response({"success": True})

        @action(detail=True, methods=["post"])
        def track_download(self, request, uuid=None):
            """Track document download."""
            doc = self.get_object()
            doc.increment_download_count()
            return Response({"success": True})

    class SellerProfileViewSet(UUIDLookupMixin, viewsets.ModelViewSet):
        """ViewSet for SellerProfile CRUD."""

        permission_classes = [IsAuthenticated, IsSellerOrAdmin]
        serializer_class = SellerProfileSerializer
        queryset = SellerProfile.objects.filter(is_active=True)

        @action(detail=False, methods=["get"])
        def me(self, request):
            """Get the current user's seller profile."""
            try:
                profile = SellerProfile.objects.get(user_id=request.user.id)
                serializer = self.get_serializer(profile)
                return Response(serializer.data)
            except SellerProfile.DoesNotExist:
                return Response(
                    {"error": "No seller profile found"}, status=status.HTTP_404_NOT_FOUND
                )

except ImportError:
    # DRF not installed
    pass
