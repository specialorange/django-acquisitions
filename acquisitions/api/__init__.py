"""
Django REST Framework API for customer acquisition.

This module is optional - requires: pip install django-acquisitions[drf]
"""

# Check if DRF is available
try:
    import rest_framework  # noqa: F401

    DRF_AVAILABLE = True
except ImportError:
    DRF_AVAILABLE = False

if DRF_AVAILABLE:
    from . import permissions, serializers, viewsets

    __all__ = ["permissions", "serializers", "viewsets"]
else:
    __all__ = []
