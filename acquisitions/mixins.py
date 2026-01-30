"""
Mixins for customer acquisition.

These mixins provide common functionality that can be used
by views and other components.
"""

from django.db import models


class TenantFilterMixin:
    """
    Mixin for filtering querysets by tenant.

    For MST-style (django-organizations): filters by account FK
    For MFT-style (django-tenants): relies on schema isolation

    Usage in views:
        class MyView(TenantFilterMixin, ListView):
            model = Lead

            def get_queryset(self):
                return self.filter_by_tenant(super().get_queryset())
    """

    tenant_field = "account"  # Override if your FK has a different name

    def get_tenant(self):
        """
        Get the current tenant.

        Override this method to return the tenant for the current request.
        For MST, this might be request.user.account or similar.
        """
        if hasattr(self.request, "tenant"):
            return self.request.tenant
        if hasattr(self.request.user, "account"):
            return self.request.user.account
        return None

    def filter_by_tenant(self, queryset):
        """Filter queryset by tenant if applicable."""
        from .settings import acquisitions_settings

        # If no tenant model configured, return as-is (MFT uses schema isolation)
        if not acquisitions_settings.TENANT_MODEL:
            return queryset

        tenant = self.get_tenant()
        if tenant:
            return queryset.filter(**{self.tenant_field: tenant})
        return queryset


class AssignedToMixin:
    """
    Mixin for filtering by assigned user.

    Usage in views:
        class MyLeadView(AssignedToMixin, ListView):
            model = Lead

            def get_queryset(self):
                return self.filter_by_assignment(super().get_queryset())
    """

    def filter_by_assignment(self, queryset, field="assigned_to_id"):
        """
        Filter queryset by assigned user.

        Args:
            queryset: The queryset to filter
            field: The field name for assignment (default: assigned_to_id)

        Checks request params for 'assigned_to':
        - 'me': Filter to current user
        - 'all': No filter (admin only)
        - <id>: Filter to specific user
        """
        assigned_to = self.request.GET.get("assigned_to", "me")

        if assigned_to == "all" and self.request.user.is_staff:
            return queryset
        elif assigned_to == "me":
            return queryset.filter(**{field: self.request.user.id})
        elif assigned_to.isdigit():
            return queryset.filter(**{field: int(assigned_to)})

        # Default to current user
        return queryset.filter(**{field: self.request.user.id})
