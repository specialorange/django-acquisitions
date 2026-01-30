"""
DRF permissions for customer acquisition.

Requires: pip install django-acquisitions[drf]
"""

try:
    from rest_framework.permissions import BasePermission, IsAuthenticated

    class HasLeadPermission(BasePermission):
        """
        Permission class for lead access.

        Override this in your project for custom permission logic.
        """

        def has_permission(self, request, view):
            return request.user and request.user.is_authenticated

        def has_object_permission(self, request, view, obj):
            # By default, authenticated users can access all leads
            # Override for tenant/organization filtering
            return True

    class IsSellerOrAdmin(BasePermission):
        """Permission for sellers or admin users."""

        def has_permission(self, request, view):
            if not request.user or not request.user.is_authenticated:
                return False

            # Admin always has access
            if request.user.is_staff or request.user.is_superuser:
                return True

            # Check if user has a seller profile
            from ..models import SellerProfile

            return SellerProfile.objects.filter(user_id=request.user.id, is_active=True).exists()

    class ReadOnlyOrAdmin(BasePermission):
        """Read-only access for regular users, full access for admins."""

        SAFE_METHODS = ("GET", "HEAD", "OPTIONS")

        def has_permission(self, request, view):
            if not request.user or not request.user.is_authenticated:
                return False

            if request.method in self.SAFE_METHODS:
                return True

            return request.user.is_staff or request.user.is_superuser

except ImportError:
    # DRF not installed
    pass
