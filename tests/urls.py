"""URL configuration for tests."""

from django.urls import include, path

urlpatterns = [
    path("api/acquisitions/", include("acquisitions.api.urls")),
]
