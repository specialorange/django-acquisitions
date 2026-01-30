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
def lead_factory(db):
    """Factory for creating test leads."""
    from acquisitions.models import Lead

    def create_lead(**kwargs):
        defaults = {
            "company_name": "Test Company",
            "status": Lead.Status.NEW,
            "source": Lead.Source.WEBSITE,
            "email": "contact@testcompany.com",
        }
        defaults.update(kwargs)
        return Lead.objects.create(**defaults)

    return create_lead


@pytest.fixture
def lead(lead_factory):
    """Create a single test lead."""
    return lead_factory()


@pytest.fixture
def contact_factory(db):
    """Factory for creating test contacts."""
    from acquisitions.models import LeadContact

    def create_contact(lead, **kwargs):
        defaults = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@testcompany.com",
        }
        defaults.update(kwargs)
        return LeadContact.objects.create(lead=lead, **defaults)

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

    def create_touchpoint(lead, **kwargs):
        defaults = {
            "touchpoint_type": Touchpoint.TouchpointType.EMAIL,
            "direction": Touchpoint.Direction.OUTBOUND,
            "occurred_at": timezone.now(),
            "performed_by_id": user.id,
        }
        defaults.update(kwargs)
        return Touchpoint.objects.create(lead=lead, **defaults)

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
