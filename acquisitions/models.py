"""
Concrete models for customer acquisition.

These models are used directly - no abstract base classes.
Projects can extend behavior through composition (signals, services, etc.)
rather than inheritance.
"""

import uuid

from django.db import models
from django.utils import timezone


class Category(models.Model):
    """Category tags for prospective clients (M2M)."""

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(
        max_length=7,
        default="#6b7280",
        help_text="Hex color code for UI display",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Industry(models.Model):
    """Industry classification for prospective clients."""

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Industry"
        verbose_name_plural = "Industries"
        ordering = ["name"]

    def __str__(self):
        return self.name


class ProspectiveClient(models.Model):
    """
    A prospective client in the acquisition pipeline.

    This is the core model - represents companies/individuals you're trying to acquire.
    """

    class Status(models.TextChoices):
        NEW = "new", "New"
        CONTACTED = "contacted", "Contacted"
        QUALIFIED = "qualified", "Qualified"
        PROPOSAL = "proposal", "Proposal Sent"
        NEGOTIATION = "negotiation", "Negotiation"
        WON = "won", "Won (Converted)"
        LOST = "lost", "Lost"
        DORMANT = "dormant", "Dormant"

    class Source(models.TextChoices):
        REFERRAL = "referral", "Referral"
        WEBSITE = "website", "Website"
        COLD_CALL = "cold_call", "Cold Call"
        TRADE_SHOW = "trade_show", "Trade Show"
        SOCIAL_MEDIA = "social", "Social Media"
        ADVERTISEMENT = "ad", "Advertisement"
        OTHER = "other", "Other"

    # UUID for external references
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)

    # Basic Information
    company_name = models.CharField(max_length=200)
    industry = models.ForeignKey(
        Industry,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="prospective_clients",
    )
    categories = models.ManyToManyField(
        Category,
        blank=True,
        related_name="prospective_clients",
    )
    website = models.URLField(blank=True)

    # Status and Pipeline
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
        db_index=True,
    )
    source = models.CharField(
        max_length=20,
        choices=Source.choices,
        default=Source.OTHER,
    )

    # Address
    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=50, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=2, default="US")

    # Scoring and Priority
    score = models.PositiveIntegerField(
        default=0,
        help_text="Score (higher = more qualified)",
    )
    priority = models.PositiveIntegerField(
        default=5,
        help_text="Priority 1-10 (1 = highest priority)",
    )

    # Estimated Value
    estimated_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Estimated annual contract value",
    )

    # Notes
    notes = models.TextField(blank=True)

    # Assignment (stores user ID from get_user_model())
    assigned_to_id = models.IntegerField(
        blank=True,
        null=True,
        db_index=True,
        help_text="User ID of assigned seller",
    )

    # Conversion tracking
    converted_at = models.DateTimeField(blank=True, null=True)
    converted_to_id = models.IntegerField(
        blank=True,
        null=True,
        help_text="ID of the account/customer after conversion",
    )

    # Sample data flag
    is_sample = models.BooleanField(
        default=False,
        help_text="Sample prospective client created during setup",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["priority", "-score", "-created_at"]
        indexes = [
            models.Index(fields=["status", "priority"]),
            models.Index(fields=["assigned_to_id", "status"]),
        ]
        verbose_name = "Prospective Client"
        verbose_name_plural = "Prospective Clients"

    def __str__(self):
        return self.company_name

    @property
    def is_active(self):
        """Check if prospective client is in an active pipeline stage."""
        return self.status not in [self.Status.WON, self.Status.LOST, self.Status.DORMANT]

    @property
    def is_converted(self):
        """Check if prospective client has been converted to a customer."""
        return self.status == self.Status.WON and self.converted_at is not None

    def mark_converted(self, customer_id=None):
        """Mark this prospective client as converted to a customer."""
        self.status = self.Status.WON
        self.converted_at = timezone.now()
        if customer_id:
            self.converted_to_id = customer_id
        self.save(update_fields=["status", "converted_at", "converted_to_id", "updated_at"])


class ProspectiveClientContact(models.Model):
    """
    Contact person associated with a prospective client.

    Multiple contacts per prospective client/company - tracks decision makers, influencers, etc.
    """

    class Role(models.TextChoices):
        DECISION_MAKER = "decision_maker", "Decision Maker"
        INFLUENCER = "influencer", "Influencer"
        CHAMPION = "champion", "Champion"
        END_USER = "end_user", "End User"
        GATEKEEPER = "gatekeeper", "Gatekeeper"
        OTHER = "other", "Other"

    # UUID for external references
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)

    # Foreign key to ProspectiveClient
    prospective_client = models.ForeignKey(
        ProspectiveClient,
        on_delete=models.CASCADE,
        related_name="contacts",
    )

    # Basic Info
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    title = models.CharField(max_length=100, blank=True)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.OTHER,
    )

    # Contact Info
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    phone_mobile = models.CharField(max_length=20, blank=True)

    # Preferences
    is_primary = models.BooleanField(default=False)
    preferred_contact_method = models.CharField(
        max_length=10,
        choices=[("email", "Email"), ("phone", "Phone"), ("sms", "SMS")],
        default="email",
    )
    best_time_to_contact = models.CharField(max_length=100, blank=True)

    # Opt-out flags
    opted_out_email = models.BooleanField(default=False)
    opted_out_sms = models.BooleanField(default=False)
    opted_out_phone = models.BooleanField(default=False)

    notes = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_primary", "last_name", "first_name"]
        verbose_name = "Prospective Client Contact"
        verbose_name_plural = "Prospective Client Contacts"

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def save(self, *args, **kwargs):
        # If this contact is primary, unset other primary contacts for this prospective client
        if self.is_primary and self.prospective_client_id:
            ProspectiveClientContact.objects.filter(
                prospective_client_id=self.prospective_client_id, is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)


class Touchpoint(models.Model):
    """
    Record of outreach/interaction with a prospective client.

    Tracks all communications: calls, emails, meetings, etc.
    """

    class TouchpointType(models.TextChoices):
        EMAIL = "email", "Email"
        PHONE = "phone", "Phone Call"
        SMS = "sms", "SMS/Text"
        MEETING = "meeting", "Meeting"
        VIDEO_CALL = "video", "Video Call"
        SOCIAL = "social", "Social Media"
        MAIL = "mail", "Physical Mail"
        OTHER = "other", "Other"

    class Direction(models.TextChoices):
        OUTBOUND = "outbound", "Outbound (We contacted them)"
        INBOUND = "inbound", "Inbound (They contacted us)"

    class Outcome(models.TextChoices):
        SUCCESSFUL = "success", "Successful"
        NO_ANSWER = "no_answer", "No Answer"
        VOICEMAIL = "voicemail", "Left Voicemail"
        BOUNCED = "bounced", "Email Bounced"
        DECLINED = "declined", "Declined/Not Interested"
        FOLLOW_UP = "follow_up", "Requires Follow-up"
        PENDING = "pending", "Pending Response"

    # UUID for external references
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)

    # Foreign key to ProspectiveClient
    prospective_client = models.ForeignKey(
        ProspectiveClient,
        on_delete=models.CASCADE,
        related_name="touchpoints",
    )

    # Type and Direction
    touchpoint_type = models.CharField(
        max_length=20,
        choices=TouchpointType.choices,
    )
    direction = models.CharField(
        max_length=10,
        choices=Direction.choices,
        default=Direction.OUTBOUND,
    )
    outcome = models.CharField(
        max_length=20,
        choices=Outcome.choices,
        blank=True,
    )

    # Optional contact reference
    contact = models.ForeignKey(
        ProspectiveClientContact,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="touchpoints",
        help_text="Specific contact person if applicable",
    )

    # Content
    subject = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)

    # Timing
    occurred_at = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Duration of call/meeting in minutes",
    )

    # Performer (stores user ID)
    performed_by_id = models.IntegerField(
        blank=True,
        null=True,
        help_text="User ID who performed this touchpoint",
    )

    # Automation tracking
    is_automated = models.BooleanField(
        default=False,
        help_text="Was this touchpoint automated (vs manual)?",
    )
    campaign = models.ForeignKey(
        "OutreachCampaign",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="touchpoints",
    )

    # External references (for tracking)
    external_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="External message ID (Twilio SID, email message-id, etc.)",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-occurred_at"]
        indexes = [
            models.Index(fields=["touchpoint_type", "occurred_at"]),
            models.Index(fields=["prospective_client", "occurred_at"]),
        ]
        verbose_name = "Touchpoint"
        verbose_name_plural = "Touchpoints"

    def __str__(self):
        return f"{self.get_touchpoint_type_display()} - {self.occurred_at.date()}"


class OutreachCampaign(models.Model):
    """
    Automated outreach campaign/sequence.

    Defines a series of touchpoints to be executed automatically.
    """

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ACTIVE = "active", "Active"
        PAUSED = "paused", "Paused"
        COMPLETED = "completed", "Completed"
        ARCHIVED = "archived", "Archived"

    # UUID for external references
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    # Timing
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)

    # Settings
    max_contacts_per_day = models.PositiveIntegerField(
        default=50,
        help_text="Maximum outreach attempts per day",
    )

    created_by_id = models.IntegerField(blank=True, null=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Outreach Campaign"
        verbose_name_plural = "Outreach Campaigns"

    def __str__(self):
        return self.name


class CampaignStep(models.Model):
    """
    A step within an outreach campaign.

    Defines what action to take and when.
    """

    class StepType(models.TextChoices):
        EMAIL = "email", "Send Email"
        SMS = "sms", "Send SMS"
        TASK = "task", "Create Task (Manual)"
        WAIT = "wait", "Wait Period"

    campaign = models.ForeignKey(
        OutreachCampaign,
        on_delete=models.CASCADE,
        related_name="steps",
    )

    # Step Details
    step_order = models.PositiveIntegerField()
    step_type = models.CharField(
        max_length=20,
        choices=StepType.choices,
    )

    # Timing
    delay_days = models.PositiveIntegerField(
        default=0,
        help_text="Days to wait after previous step",
    )
    delay_hours = models.PositiveIntegerField(
        default=0,
        help_text="Additional hours to wait",
    )

    # Content (for email/SMS steps)
    subject_template = models.CharField(max_length=255, blank=True)
    body_template = models.TextField(blank=True)

    # Conditions
    skip_if_responded = models.BooleanField(
        default=True,
        help_text="Skip this step if lead has responded",
    )

    is_active = models.BooleanField(default=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["step_order"]
        unique_together = [["campaign", "step_order"]]
        verbose_name = "Campaign Step"
        verbose_name_plural = "Campaign Steps"

    def __str__(self):
        return f"Step {self.step_order}: {self.get_step_type_display()}"

    @property
    def total_delay_hours(self):
        """Total delay in hours."""
        return (self.delay_days * 24) + self.delay_hours


class CampaignEnrollment(models.Model):
    """Tracks which prospective clients are enrolled in which campaigns."""

    prospective_client = models.ForeignKey(
        ProspectiveClient,
        on_delete=models.CASCADE,
        related_name="campaign_enrollments",
    )
    campaign = models.ForeignKey(
        OutreachCampaign,
        on_delete=models.CASCADE,
        related_name="enrollments",
    )

    # Progress tracking
    current_step = models.PositiveIntegerField(default=0)
    next_step_scheduled_at = models.DateTimeField(blank=True, null=True)

    # Status
    is_active = models.BooleanField(default=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    # Timestamps
    enrolled_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [["prospective_client", "campaign"]]
        ordering = ["-enrolled_at"]
        verbose_name = "Campaign Enrollment"
        verbose_name_plural = "Campaign Enrollments"

    def __str__(self):
        return f"{self.prospective_client} in {self.campaign}"


class MarketingDocument(models.Model):
    """
    Marketing/sales document to help sell services.

    Brochures, case studies, pricing sheets, etc.
    """

    class DocumentType(models.TextChoices):
        BROCHURE = "brochure", "Brochure"
        CASE_STUDY = "case_study", "Case Study"
        PRICING = "pricing", "Pricing Sheet"
        PROPOSAL_TEMPLATE = "proposal", "Proposal Template"
        PRESENTATION = "presentation", "Presentation"
        ONE_PAGER = "one_pager", "One-Pager"
        FAQ = "faq", "FAQ"
        OTHER = "other", "Other"

    # UUID for external references
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)

    name = models.CharField(max_length=200)
    document_type = models.CharField(
        max_length=20,
        choices=DocumentType.choices,
    )
    description = models.TextField(blank=True)

    # File
    file = models.FileField(
        upload_to="acquisitions/documents/",
        blank=True,
        null=True,
    )
    external_url = models.URLField(
        blank=True,
        help_text="External URL (if not uploaded)",
    )

    # Versioning
    version = models.CharField(max_length=20, default="1.0")

    # Access Control
    is_internal_only = models.BooleanField(
        default=False,
        help_text="Only visible to internal sellers",
    )
    is_active = models.BooleanField(default=True)

    # Usage tracking
    view_count = models.PositiveIntegerField(default=0)
    download_count = models.PositiveIntegerField(default=0)

    created_by_id = models.IntegerField(blank=True, null=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["document_type", "name"]
        verbose_name = "Marketing Document"
        verbose_name_plural = "Marketing Documents"

    def __str__(self):
        return f"{self.name} (v{self.version})"

    def increment_view_count(self):
        """Increment view count atomically."""
        MarketingDocument.objects.filter(pk=self.pk).update(
            view_count=models.F("view_count") + 1
        )

    def increment_download_count(self):
        """Increment download count atomically."""
        MarketingDocument.objects.filter(pk=self.pk).update(
            download_count=models.F("download_count") + 1
        )


class SellerProfile(models.Model):
    """
    Internal seller profile for automation.

    Links a user to their selling preferences and automation settings.
    """

    # UUID for external references
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)

    user_id = models.IntegerField(
        unique=True,
        db_index=True,
        help_text="User ID from get_user_model()",
    )

    # Display info (denormalized for performance)
    display_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)

    # Email signature
    email_signature = models.TextField(
        blank=True,
        help_text="HTML signature for outreach emails",
    )

    # Automation preferences
    auto_assign_prospective_clients = models.BooleanField(
        default=False,
        help_text="Automatically assign new prospective clients to this seller",
    )
    max_active_prospective_clients = models.PositiveIntegerField(
        default=50,
        help_text="Maximum prospective clients in active pipeline",
    )

    # Working hours (for scheduling outreach)
    working_hours_start = models.TimeField(default="09:00")
    working_hours_end = models.TimeField(default="17:00")
    working_days = models.CharField(
        max_length=20,
        default="1,2,3,4,5",
        help_text="Comma-separated days (1=Mon, 7=Sun)",
    )
    timezone = models.CharField(max_length=50, default="America/New_York")

    # Stats (denormalized for dashboard)
    total_converted = models.PositiveIntegerField(default=0)
    active_prospective_clients_count = models.PositiveIntegerField(default=0)

    is_active = models.BooleanField(default=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Seller Profile"
        verbose_name_plural = "Seller Profiles"

    def __str__(self):
        return self.display_name

    def get_working_days_list(self):
        """Return working days as list of integers."""
        return [int(d) for d in self.working_days.split(",") if d.strip()]
