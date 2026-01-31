Quick Start
===========

This guide will help you get started with django-acquisitions.

Setup
-----

1. Add ``acquisitions`` to your ``INSTALLED_APPS`` in ``settings.py``:

.. code-block:: python

   INSTALLED_APPS = [
       ...
       'acquisitions',
   ]

2. Run migrations:

.. code-block:: bash

   python manage.py migrate acquisitions

3. Optionally, include the URLs for the REST API:

.. code-block:: python

   from django.urls import path, include

   urlpatterns = [
       ...
       path('api/acquisitions/', include('acquisitions.api.urls')),
   ]


Creating Prospective Clients
----------------------------

.. code-block:: python

   from acquisitions.models import ProspectiveClient, Industry, Category

   # Create an industry
   tech = Industry.objects.create(name="Technology")

   # Create categories
   enterprise = Category.objects.create(name="Enterprise", color="#3b82f6")
   high_value = Category.objects.create(name="High Value", color="#22c55e")

   # Create a prospective client
   pc = ProspectiveClient.objects.create(
       company_name="Acme Corp",
       industry=tech,
       status=ProspectiveClient.Status.NEW,
       source=ProspectiveClient.Source.REFERRAL,
       website="https://acme.com",
       estimated_value=50000,
       priority=1,
   )

   # Add categories
   pc.categories.add(enterprise, high_value)


Adding Contacts
---------------

.. code-block:: python

   from acquisitions.models import ProspectiveClientContact

   # Add primary contact
   contact = ProspectiveClientContact.objects.create(
       prospective_client=pc,
       first_name="Jane",
       last_name="Doe",
       title="VP of Operations",
       role=ProspectiveClientContact.Role.DECISION_MAKER,
       email="jane@acme.com",
       phone="555-123-4567",
       is_primary=True,
   )

   # Add secondary contact
   ProspectiveClientContact.objects.create(
       prospective_client=pc,
       first_name="Bob",
       last_name="Smith",
       title="IT Manager",
       role=ProspectiveClientContact.Role.INFLUENCER,
       email="bob@acme.com",
   )


Recording Touchpoints
---------------------

.. code-block:: python

   from acquisitions.models import Touchpoint
   from django.utils import timezone

   # Record an email
   Touchpoint.objects.create(
       prospective_client=pc,
       contact=contact,
       touchpoint_type=Touchpoint.TouchpointType.EMAIL,
       direction=Touchpoint.Direction.OUTBOUND,
       outcome=Touchpoint.Outcome.PENDING,
       subject="Introduction to Our Services",
       notes="Sent product overview and pricing",
       occurred_at=timezone.now(),
       performed_by_id=request.user.id,
   )

   # Record a phone call
   Touchpoint.objects.create(
       prospective_client=pc,
       contact=contact,
       touchpoint_type=Touchpoint.TouchpointType.PHONE,
       direction=Touchpoint.Direction.OUTBOUND,
       outcome=Touchpoint.Outcome.SUCCESSFUL,
       notes="Discussed requirements, scheduled demo for next week",
       occurred_at=timezone.now(),
       duration_minutes=30,
       performed_by_id=request.user.id,
   )


Managing the Pipeline
---------------------

.. code-block:: python

   # Move through the pipeline
   pc.status = ProspectiveClient.Status.CONTACTED
   pc.save()

   pc.status = ProspectiveClient.Status.QUALIFIED
   pc.save()

   # Check if still active in pipeline
   if pc.is_active:
       print("Still working this prospect")

   # Convert to customer
   pc.mark_converted(customer_id=123)

   # Check conversion status
   if pc.is_converted:
       print(f"Converted on {pc.converted_at}")


Setting Up Outreach Campaigns
-----------------------------

.. code-block:: python

   from acquisitions.models import OutreachCampaign, CampaignStep, CampaignEnrollment

   # Create a campaign
   campaign = OutreachCampaign.objects.create(
       name="New Prospect Welcome Series",
       status=OutreachCampaign.Status.ACTIVE,
       max_contacts_per_day=50,
   )

   # Add steps
   CampaignStep.objects.create(
       campaign=campaign,
       step_order=0,
       step_type=CampaignStep.StepType.EMAIL,
       delay_days=0,
       subject_template="Welcome {{ company_name }}!",
       body_template="Hi {{ first_name }}, thanks for your interest...",
   )

   CampaignStep.objects.create(
       campaign=campaign,
       step_order=1,
       step_type=CampaignStep.StepType.EMAIL,
       delay_days=3,
       subject_template="Following up",
       body_template="Just checking in...",
       skip_if_responded=True,
   )

   CampaignStep.objects.create(
       campaign=campaign,
       step_order=2,
       step_type=CampaignStep.StepType.SMS,
       delay_days=7,
       body_template="Hi {{ first_name }}, quick reminder about our services.",
       skip_if_responded=True,
   )

   # Enroll a prospective client
   enrollment = CampaignEnrollment.objects.create(
       prospective_client=pc,
       campaign=campaign,
   )


Using Services
--------------

.. code-block:: python

   from acquisitions.services.outreach import enroll_prospective_client_in_campaign
   from acquisitions.services.onboarding import convert_prospective_client

   # Enroll in campaign (handles scheduling)
   enrollment = enroll_prospective_client_in_campaign(pc, campaign)

   # Convert to customer
   result = convert_prospective_client(pc, request.user)
   if result["success"]:
       print("Conversion successful!")


Querying Prospective Clients
----------------------------

.. code-block:: python

   # Get all active prospects
   active = ProspectiveClient.objects.exclude(
       status__in=[
           ProspectiveClient.Status.WON,
           ProspectiveClient.Status.LOST,
           ProspectiveClient.Status.DORMANT,
       ]
   )

   # Get high priority prospects
   high_priority = ProspectiveClient.objects.filter(priority__lte=3)

   # Get prospects by industry
   tech_prospects = ProspectiveClient.objects.filter(industry__name="Technology")

   # Get prospects with specific category
   enterprise = ProspectiveClient.objects.filter(categories__name="Enterprise")

   # Get prospects assigned to current user
   my_prospects = ProspectiveClient.objects.filter(assigned_to_id=request.user.id)
