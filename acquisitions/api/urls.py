"""
URL configuration for acquisitions API.

Requires: pip install django-acquisitions[drf]
"""

try:
    from django.urls import include, path
    from rest_framework.routers import DefaultRouter

    from .viewsets import (
        DashboardViewSet,
        MarketingDocumentViewSet,
        OutreachCampaignViewSet,
        ProspectiveClientContactViewSet,
        ProspectiveClientViewSet,
        SellerProfileViewSet,
        TouchpointViewSet,
    )

    router = DefaultRouter()
    router.register(r"prospective-clients", ProspectiveClientViewSet, basename="prospective-client")
    router.register(r"campaigns", OutreachCampaignViewSet, basename="campaign")
    router.register(r"documents", MarketingDocumentViewSet, basename="document")
    router.register(r"sellers", SellerProfileViewSet, basename="seller")
    router.register(r"dashboard", DashboardViewSet, basename="dashboard")

    # Nested routes for prospective client contacts and touchpoints
    contacts_list = ProspectiveClientContactViewSet.as_view({"get": "list", "post": "create"})
    contacts_detail = ProspectiveClientContactViewSet.as_view(
        {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
    )

    touchpoints_list = TouchpointViewSet.as_view({"get": "list", "post": "create"})
    touchpoints_detail = TouchpointViewSet.as_view(
        {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
    )

    urlpatterns = [
        path("", include(router.urls)),
        # Nested routes
        path(
            "prospective-clients/<uuid:prospective_client_uuid>/contacts/",
            contacts_list,
            name="prospective-client-contacts-list",
        ),
        path(
            "prospective-clients/<uuid:prospective_client_uuid>/contacts/<uuid:uuid>/",
            contacts_detail,
            name="prospective-client-contacts-detail",
        ),
        path(
            "prospective-clients/<uuid:prospective_client_uuid>/touchpoints/",
            touchpoints_list,
            name="prospective-client-touchpoints-list",
        ),
        path(
            "prospective-clients/<uuid:prospective_client_uuid>/touchpoints/<uuid:uuid>/",
            touchpoints_detail,
            name="prospective-client-touchpoints-detail",
        ),
    ]

except ImportError:
    # DRF not installed
    urlpatterns = []
