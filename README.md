# django-acquisitions

[![Tests](https://github.com/specialorange/django-acquisitions/actions/workflows/tests.yml/badge.svg)](https://github.com/specialorange/django-acquisitions/actions/workflows/tests.yml)
[![codecov](https://codecov.io/gh/specialorange/django-acquisitions/graph/badge.svg)](https://codecov.io/gh/specialorange/django-acquisitions)
[![Documentation Status](https://readthedocs.org/projects/django-acquisitions/badge/?version=latest)](https://django-acquisitions.readthedocs.io/en/latest/)
[![PyPI version](https://badge.fury.io/py/django-acquisitions.svg)](https://pypi.org/project/django-acquisitions/)

A minimal Django 4+ package for customer acquisition pipeline management. Track leads, manage contacts, automate outreach campaigns, and handle customer onboarding.

## Features

- **Lead Management** - Track potential customers through your acquisition pipeline
- **Contact Management** - Multiple contacts per lead (decision makers, influencers, etc.)
- **Touchpoint Tracking** - Record all outreach (calls, emails, SMS, meetings)
- **Outreach Campaigns** - Automated multi-step sequences with email/SMS
- **Marketing Documents** - Manage brochures, case studies, proposals
- **Seller Profiles** - Internal profiles for automation preferences
- **Onboarding Handoff** - Convert leads to customers with callbacks

## Installation

```bash
pip install django-acquisitions
```

With optional dependencies:

```bash
# With Celery support for async tasks
pip install django-acquisitions[celery]

# With Twilio for SMS
pip install django-acquisitions[twilio]

# With Django REST Framework for API
pip install django-acquisitions[drf]

# All optional dependencies
pip install django-acquisitions[all]
```

## Quick Start

1. Add to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ...
    'acquisitions',
]
```

2. Run migrations:

```bash
python manage.py migrate acquisitions
```

3. Configure settings (optional):

```python
# settings.py

# For multi-tenant (MST-style with django-organizations)
ACQUISITIONS_TENANT_MODEL = 'accounts.Account'

# For schema-per-tenant (MFT-style with django-tenants)
ACQUISITIONS_TENANT_MODEL = None  # Uses schema isolation

# Communication backends
ACQUISITIONS_EMAIL_BACKEND = 'acquisitions.backends.email.django_email.DjangoEmailBackend'
ACQUISITIONS_SMS_BACKEND = 'acquisitions.backends.sms.twilio.TwilioBackend'

# Twilio settings (if using Twilio backend)
TWILIO_ACCOUNT_SID = 'your-account-sid'
TWILIO_AUTH_TOKEN = 'your-auth-token'
TWILIO_FROM_NUMBER = '+1234567890'

# Celery settings
ACQUISITIONS_USE_CELERY = True

# Onboarding callback (called when lead converts to customer)
ACQUISITIONS_ONBOARDING_CALLBACK = 'myapp.services.create_customer_from_lead'
```

## Models

### Lead

The core model representing a potential customer:

```python
from acquisitions.models import Lead

lead = Lead.objects.create(
    company_name='Acme Corp',
    email='contact@acme.com',
    status=Lead.Status.NEW,
    source=Lead.Source.WEBSITE,
)
```

### LeadContact

Multiple contacts per lead:

```python
from acquisitions.models import LeadContact

contact = LeadContact.objects.create(
    lead=lead,
    first_name='John',
    last_name='Doe',
    title='VP of Operations',
    role=LeadContact.Role.DECISION_MAKER,
    email='john@acme.com',
    is_primary=True,
)
```

### Touchpoint

Track all interactions:

```python
from acquisitions.models import Touchpoint
from django.utils import timezone

touchpoint = Touchpoint.objects.create(
    lead=lead,
    touchpoint_type=Touchpoint.TouchpointType.EMAIL,
    direction=Touchpoint.Direction.OUTBOUND,
    subject='Introduction to our services',
    occurred_at=timezone.now(),
    performed_by_id=request.user.id,
)
```

### OutreachCampaign

Automated sequences:

```python
from acquisitions.models import OutreachCampaign, CampaignStep

campaign = OutreachCampaign.objects.create(
    name='New Lead Nurture',
    status=OutreachCampaign.Status.ACTIVE,
)

CampaignStep.objects.create(
    campaign=campaign,
    step_order=1,
    step_type=CampaignStep.StepType.EMAIL,
    delay_days=0,
    subject_template='Welcome to {{ company_name }}!',
    body_template='Hi {{ contact.first_name }}, ...',
)
```

## API Endpoints

When using with Django REST Framework:

```python
# urls.py
from django.urls import path, include

urlpatterns = [
    path('api/acquisitions/', include('acquisitions.api.urls')),
]
```

Available endpoints:

- `GET/POST /api/acquisitions/leads/` - List/create leads
- `GET/PUT/DELETE /api/acquisitions/leads/{uuid}/` - Lead detail
- `POST /api/acquisitions/leads/{uuid}/convert/` - Convert to customer
- `POST /api/acquisitions/leads/{uuid}/enroll_campaign/` - Enroll in campaign
- `GET/POST /api/acquisitions/leads/{uuid}/contacts/` - Lead contacts
- `GET/POST /api/acquisitions/leads/{uuid}/touchpoints/` - Lead touchpoints
- `GET/POST /api/acquisitions/campaigns/` - Outreach campaigns
- `GET/POST /api/acquisitions/documents/` - Marketing documents

## Celery Tasks

For automated outreach, add to your Celery beat schedule:

```python
# celery.py or settings.py
CELERY_BEAT_SCHEDULE = {
    'process_acquisitions_outreach': {
        'task': 'acquisitions.tasks.outreach_tasks.process_scheduled_outreach',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
}
```

## Custom Models

Use abstract models to add custom fields:

```python
# myapp/models.py
from acquisitions.abstract_models import AbstractLead
from myapp.models import Account

class Lead(AbstractLead):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    custom_field = models.CharField(max_length=100)

    class Meta(AbstractLead.Meta):
        abstract = False
```

Then configure:

```python
ACQUISITIONS_LEAD_MODEL = 'myapp.Lead'
```

## License

BSD-3-Clause

