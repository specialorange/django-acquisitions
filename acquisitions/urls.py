"""
URL configuration for acquisitions app.

Include these in your project's urls.py:

    from django.urls import include, path

    urlpatterns = [
        # API endpoints (requires DRF)
        path('api/acquisitions/', include('acquisitions.api.urls')),
    ]
"""

from django.urls import include, path

app_name = "acquisitions"

urlpatterns = []

# Include API URLs if DRF is available
try:
    from .api import DRF_AVAILABLE

    if DRF_AVAILABLE:
        urlpatterns += [
            path("api/", include("acquisitions.api.urls")),
        ]
except ImportError:
    pass
