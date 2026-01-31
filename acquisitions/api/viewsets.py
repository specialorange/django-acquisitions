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
        MarketingDocument,
        OutreachCampaign,
        ProspectiveClient,
        ProspectiveClientContact,
        SellerProfile,
        Touchpoint,
    )
    from .permissions import HasProspectiveClientPermission, IsSellerOrAdmin, ReadOnlyOrAdmin
    from .serializers import (
        MarketingDocumentSerializer,
        OutreachCampaignSerializer,
        ProspectiveClientContactSerializer,
        ProspectiveClientCreateSerializer,
        ProspectiveClientDetailSerializer,
        ProspectiveClientListSerializer,
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

    class ProspectiveClientViewSet(UUIDLookupMixin, MultiSerializerMixin, viewsets.ModelViewSet):
        """
        ViewSet for ProspectiveClient CRUD operations.

        list: List all prospective clients (with filtering)
        retrieve: Get prospective client details
        create: Create new prospective client
        update: Update prospective client
        destroy: Delete prospective client
        """

        permission_classes = [IsAuthenticated, HasProspectiveClientPermission]
        serializer_class = ProspectiveClientListSerializer
        serializer_classes = {
            "list": ProspectiveClientListSerializer,
            "retrieve": ProspectiveClientDetailSerializer,
            "create": ProspectiveClientCreateSerializer,
            "update": ProspectiveClientDetailSerializer,
            "partial_update": ProspectiveClientDetailSerializer,
        }

        def get_queryset(self):
            """Filter queryset based on query params."""
            qs = ProspectiveClient.objects.all()

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
            """Convert a prospective client to a customer."""
            prospective_client = self.get_object()

            from ..services.onboarding import convert_prospective_client

            result = convert_prospective_client(prospective_client, request.user)

            if result["success"]:
                return Response(
                    {
                        "success": True,
                        "prospective_client_uuid": str(prospective_client.uuid),
                        "customer_id": result.get("customer_id"),
                    }
                )
            else:
                return Response({"error": result.get("error")}, status=status.HTTP_400_BAD_REQUEST)

        @action(detail=True, methods=["post"])
        def enroll_campaign(self, request, uuid=None):
            """Enroll prospective client in an outreach campaign."""
            prospective_client = self.get_object()
            campaign_uuid = request.data.get("campaign_uuid")

            if not campaign_uuid:
                return Response(
                    {"error": "campaign_uuid required"}, status=status.HTTP_400_BAD_REQUEST
                )

            try:
                campaign = OutreachCampaign.objects.get(uuid=campaign_uuid)
            except OutreachCampaign.DoesNotExist:
                return Response({"error": "Campaign not found"}, status=status.HTTP_404_NOT_FOUND)

            from ..services.outreach import enroll_prospective_client_in_campaign

            try:
                enrollment = enroll_prospective_client_in_campaign(prospective_client, campaign)
                return Response(
                    {
                        "success": True,
                        "enrollment_id": enrollment.id,
                    }
                )
            except ValueError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    class ProspectiveClientContactViewSet(UUIDLookupMixin, viewsets.ModelViewSet):
        """ViewSet for ProspectiveClientContact CRUD."""

        permission_classes = [IsAuthenticated]
        serializer_class = ProspectiveClientContactSerializer

        def get_queryset(self):
            prospective_client_uuid = self.kwargs.get("lead_uuid")  # Keep URL param name for backwards compat
            if prospective_client_uuid:
                return ProspectiveClientContact.objects.filter(prospective_client__uuid=prospective_client_uuid)
            return ProspectiveClientContact.objects.none()

        def perform_create(self, serializer):
            prospective_client_uuid = self.kwargs.get("lead_uuid")
            prospective_client = ProspectiveClient.objects.get(uuid=prospective_client_uuid)
            serializer.save(prospective_client=prospective_client)

    class TouchpointViewSet(UUIDLookupMixin, viewsets.ModelViewSet):
        """ViewSet for Touchpoint CRUD."""

        permission_classes = [IsAuthenticated]
        serializer_class = TouchpointSerializer

        def get_queryset(self):
            prospective_client_uuid = self.kwargs.get("lead_uuid")  # Keep URL param name for backwards compat
            if prospective_client_uuid:
                return Touchpoint.objects.filter(prospective_client__uuid=prospective_client_uuid)
            return Touchpoint.objects.all()

        def perform_create(self, serializer):
            prospective_client_uuid = self.kwargs.get("lead_uuid")
            if prospective_client_uuid:
                prospective_client = ProspectiveClient.objects.get(uuid=prospective_client_uuid)
                serializer.save(
                    prospective_client=prospective_client,
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
