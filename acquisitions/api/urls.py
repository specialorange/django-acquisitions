"""
URL configuration for acquisitions API.

Requires: pip install django-acquisitions[drf]
"""

try:
    from django.urls import include, path
    from rest_framework.routers import DefaultRouter

    from .viewsets import (
        LeadContactViewSet,
        LeadViewSet,
        MarketingDocumentViewSet,
        OutreachCampaignViewSet,
        SellerProfileViewSet,
        TouchpointViewSet,
    )

    router = DefaultRouter()
    router.register(r"leads", LeadViewSet, basename="lead")
    router.register(r"campaigns", OutreachCampaignViewSet, basename="campaign")
    router.register(r"documents", MarketingDocumentViewSet, basename="document")
    router.register(r"sellers", SellerProfileViewSet, basename="seller")

    # Nested routes for lead contacts and touchpoints
    lead_contacts_list = LeadContactViewSet.as_view({"get": "list", "post": "create"})
    lead_contacts_detail = LeadContactViewSet.as_view(
        {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
    )

    lead_touchpoints_list = TouchpointViewSet.as_view({"get": "list", "post": "create"})
    lead_touchpoints_detail = TouchpointViewSet.as_view(
        {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
    )

    urlpatterns = [
        path("", include(router.urls)),
        # Nested routes
        path(
            "leads/<uuid:lead_uuid>/contacts/",
            lead_contacts_list,
            name="lead-contacts-list",
        ),
        path(
            "leads/<uuid:lead_uuid>/contacts/<uuid:uuid>/",
            lead_contacts_detail,
            name="lead-contacts-detail",
        ),
        path(
            "leads/<uuid:lead_uuid>/touchpoints/",
            lead_touchpoints_list,
            name="lead-touchpoints-list",
        ),
        path(
            "leads/<uuid:lead_uuid>/touchpoints/<uuid:uuid>/",
            lead_touchpoints_detail,
            name="lead-touchpoints-detail",
        ),
    ]

except ImportError:
    # DRF not installed
    urlpatterns = []
