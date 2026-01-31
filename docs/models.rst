Models
======

django-acquisitions provides models for managing customer acquisition pipelines.

ProspectiveClient
-----------------

The core model representing a potential customer in your acquisition pipeline.

**Status Workflow:**

- ``new`` - Just entered the pipeline
- ``contacted`` - Initial outreach made
- ``qualified`` - Confirmed as a good fit
- ``proposal`` - Proposal sent
- ``negotiation`` - In active negotiation
- ``won`` - Successfully converted to customer
- ``lost`` - Did not convert
- ``dormant`` - Inactive, may revisit later

**Source Tracking:**

Track where prospective clients come from: referral, website, cold call, trade show, social media, advertisement, or other.

**Key Features:**

- UUID for external/API references
- Industry classification (FK)
- Multiple category tags (M2M)
- Scoring and priority for pipeline management
- Estimated contract value
- Assignment to sellers
- Conversion tracking with timestamps

.. note::

   ``Lead`` is available as a backwards-compatible alias for ``ProspectiveClient``.

Example::

    from acquisitions.models import ProspectiveClient

    pc = ProspectiveClient.objects.create(
        company_name="Acme Corp",
        status=ProspectiveClient.Status.NEW,
        source=ProspectiveClient.Source.WEBSITE,
        priority=1,
        score=85,
    )

    # Check if active in pipeline
    if pc.is_active:
        print("Still working this prospect")

    # Convert to customer
    pc.mark_converted(customer_id=123)


ProspectiveClientContact
------------------------

Contact person associated with a prospective client. Supports multiple contacts per company.

**Roles:**

- ``decision_maker`` - Has authority to make purchasing decisions
- ``influencer`` - Influences the decision
- ``champion`` - Internal advocate for your solution
- ``end_user`` - Will use the product/service
- ``gatekeeper`` - Controls access to decision makers
- ``other`` - Other role

**Key Features:**

- Primary contact designation (auto-manages uniqueness)
- Contact preferences (email, phone, SMS)
- Opt-out tracking for compliance
- Best time to contact

.. note::

   ``LeadContact`` is available as a backwards-compatible alias for ``ProspectiveClientContact``.

Example::

    from acquisitions.models import ProspectiveClientContact

    contact = ProspectiveClientContact.objects.create(
        prospective_client=pc,
        first_name="Jane",
        last_name="Doe",
        title="VP of Operations",
        role=ProspectiveClientContact.Role.DECISION_MAKER,
        email="jane@acme.com",
        is_primary=True,
    )


Touchpoint
----------

Record of every interaction with a prospective client.

**Types:**

- ``email`` - Email communication
- ``phone`` - Phone call
- ``sms`` - Text message
- ``meeting`` - In-person meeting
- ``video`` - Video call
- ``social`` - Social media interaction
- ``mail`` - Physical mail
- ``other`` - Other interaction

**Directions:**

- ``outbound`` - You contacted them
- ``inbound`` - They contacted you

**Outcomes:**

- ``success`` - Successful interaction
- ``no_answer`` - No answer
- ``voicemail`` - Left voicemail
- ``bounced`` - Email bounced
- ``declined`` - Not interested
- ``follow_up`` - Requires follow-up
- ``pending`` - Awaiting response

Example::

    from acquisitions.models import Touchpoint
    from django.utils import timezone

    touchpoint = Touchpoint.objects.create(
        prospective_client=pc,
        touchpoint_type=Touchpoint.TouchpointType.EMAIL,
        direction=Touchpoint.Direction.OUTBOUND,
        outcome=Touchpoint.Outcome.PENDING,
        subject="Introduction to our services",
        occurred_at=timezone.now(),
        performed_by_id=request.user.id,
    )


OutreachCampaign
----------------

Automated multi-step outreach sequences.

**Statuses:**

- ``draft`` - Being created, not active
- ``active`` - Running and enrolling prospects
- ``paused`` - Temporarily stopped
- ``completed`` - Finished
- ``archived`` - No longer in use

Example::

    from acquisitions.models import OutreachCampaign, CampaignStep

    campaign = OutreachCampaign.objects.create(
        name="New Lead Welcome Series",
        status=OutreachCampaign.Status.ACTIVE,
        max_contacts_per_day=50,
    )

    CampaignStep.objects.create(
        campaign=campaign,
        step_order=0,
        step_type=CampaignStep.StepType.EMAIL,
        delay_days=0,
        subject_template="Welcome {{ company_name }}!",
        body_template="Hi {{ first_name }}, ...",
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


CampaignEnrollment
------------------

Tracks which prospective clients are enrolled in which campaigns.

Example::

    from acquisitions.models import CampaignEnrollment

    enrollment = CampaignEnrollment.objects.create(
        prospective_client=pc,
        campaign=campaign,
    )


Category
--------

Tags for categorizing prospective clients (many-to-many relationship).

Example::

    from acquisitions.models import Category

    enterprise = Category.objects.create(
        name="Enterprise",
        color="#3b82f6",
        description="Large enterprise accounts",
    )

    pc.categories.add(enterprise)


Industry
--------

Industry classification for prospective clients.

Example::

    from acquisitions.models import Industry

    tech = Industry.objects.create(
        name="Technology",
        description="Software and hardware companies",
    )

    pc.industry = tech
    pc.save()


MarketingDocument
-----------------

Sales and marketing collateral for the acquisition process.

**Document Types:**

- ``brochure`` - Company/product brochure
- ``case_study`` - Customer case study
- ``pricing`` - Pricing sheet
- ``proposal`` - Proposal template
- ``presentation`` - Sales presentation
- ``one_pager`` - One-page summary
- ``faq`` - Frequently asked questions
- ``other`` - Other document

**Features:**

- File upload or external URL
- Version tracking
- Internal-only flag for confidential documents
- View and download count tracking

Example::

    from acquisitions.models import MarketingDocument

    doc = MarketingDocument.objects.create(
        name="Product Brochure 2024",
        document_type=MarketingDocument.DocumentType.BROCHURE,
        version="2.0",
        external_url="https://example.com/brochure.pdf",
    )

    # Track usage
    doc.increment_view_count()
    doc.increment_download_count()


SellerProfile
-------------

Internal seller profile for automation and preferences.

**Features:**

- Email signature for outreach
- Working hours and days for scheduling
- Timezone support
- Auto-assignment settings
- Performance stats (conversions, active prospects)

Example::

    from acquisitions.models import SellerProfile

    profile = SellerProfile.objects.create(
        user_id=user.id,
        display_name="Jane Smith",
        email="jane@company.com",
        working_hours_start="09:00",
        working_hours_end="17:00",
        working_days="1,2,3,4,5",  # Mon-Fri
        timezone="America/New_York",
    )
