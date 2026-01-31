"""
Pytest fixtures for django-acquisitions tests.
"""

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone


@pytest.fixture
def user(db):
    """Create a test user."""
    User = get_user_model()
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",  # pragma: allowlist secret
    )


@pytest.fixture
def staff_user(db):
    """Create a staff user."""
    User = get_user_model()
    return User.objects.create_user(
        username="staffuser",
        email="staff@example.com",
        password="testpass123",  # pragma: allowlist secret
        is_staff=True,
    )


@pytest.fixture
def category_factory(db):
    """Factory for creating test categories."""
    from acquisitions.models import Category

    def create_category(**kwargs):
        defaults = {
            "name": "High Value",
            "color": "#22c55e",
        }
        defaults.update(kwargs)
        return Category.objects.create(**defaults)

    return create_category


@pytest.fixture
def industry_factory(db):
    """Factory for creating test industries."""
    from acquisitions.models import Industry

    def create_industry(**kwargs):
        defaults = {
            "name": "Technology",
        }
        defaults.update(kwargs)
        return Industry.objects.create(**defaults)

    return create_industry


@pytest.fixture
def prospective_client_factory(db):
    """Factory for creating test prospective clients."""
    from acquisitions.models import ProspectiveClient

    def create_prospective_client(**kwargs):
        defaults = {
            "company_name": "Test Company",
            "status": ProspectiveClient.Status.NEW,
            "source": ProspectiveClient.Source.WEBSITE,
        }
        defaults.update(kwargs)
        return ProspectiveClient.objects.create(**defaults)

    return create_prospective_client


# Backwards compatibility alias
@pytest.fixture
def lead_factory(prospective_client_factory):
    """Factory for creating test leads (alias for prospective_client_factory)."""
    return prospective_client_factory


@pytest.fixture
def prospective_client(prospective_client_factory):
    """Create a single test prospective client."""
    return prospective_client_factory()


# Backwards compatibility alias
@pytest.fixture
def lead(prospective_client):
    """Create a single test lead (alias for prospective_client)."""
    return prospective_client


@pytest.fixture
def contact_factory(db):
    """Factory for creating test contacts."""
    from acquisitions.models import ProspectiveClientContact

    def create_contact(prospective_client, **kwargs):
        defaults = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@testcompany.com",
        }
        defaults.update(kwargs)
        return ProspectiveClientContact.objects.create(prospective_client=prospective_client, **defaults)

    return create_contact


@pytest.fixture
def campaign_factory(db, user):
    """Factory for creating test campaigns."""
    from acquisitions.models import OutreachCampaign

    def create_campaign(**kwargs):
        defaults = {
            "name": "Test Campaign",
            "status": OutreachCampaign.Status.ACTIVE,
            "created_by_id": user.id,
        }
        defaults.update(kwargs)
        return OutreachCampaign.objects.create(**defaults)

    return create_campaign


@pytest.fixture
def campaign(campaign_factory):
    """Create a single test campaign."""
    return campaign_factory()


@pytest.fixture
def campaign_step_factory(db):
    """Factory for creating campaign steps."""
    from acquisitions.models import CampaignStep

    def create_step(campaign, **kwargs):
        defaults = {
            "step_order": 0,
            "step_type": CampaignStep.StepType.EMAIL,
            "delay_days": 0,
            "subject_template": "Hello {{ company_name }}",
            "body_template": "Hi {{ first_name }}, we'd love to work with you.",
        }
        defaults.update(kwargs)
        return CampaignStep.objects.create(campaign=campaign, **defaults)

    return create_step


@pytest.fixture
def touchpoint_factory(db, user):
    """Factory for creating touchpoints."""
    from acquisitions.models import Touchpoint

    def create_touchpoint(prospective_client, **kwargs):
        defaults = {
            "touchpoint_type": Touchpoint.TouchpointType.EMAIL,
            "direction": Touchpoint.Direction.OUTBOUND,
            "occurred_at": timezone.now(),
            "performed_by_id": user.id,
        }
        defaults.update(kwargs)
        return Touchpoint.objects.create(prospective_client=prospective_client, **defaults)

    return create_touchpoint


@pytest.fixture
def seller_profile_factory(db):
    """Factory for creating seller profiles."""
    from acquisitions.models import SellerProfile

    def create_profile(user, **kwargs):
        defaults = {
            "user_id": user.id,
            "display_name": user.username,
            "email": user.email,
        }
        defaults.update(kwargs)
        return SellerProfile.objects.create(**defaults)

    return create_profile
