django-acquisitions
===================

A Django package for customer acquisition pipeline management. Track prospective clients, manage contacts, automate outreach campaigns, and handle customer onboarding.

Features
--------

**Prospective Client Management**
   Track potential customers through your acquisition pipeline with customizable statuses (new, contacted, qualified, proposal, negotiation, won, lost, dormant).

**Contact Management**
   Multiple contacts per prospective client with role tracking (decision maker, influencer, champion, end user, gatekeeper).

**Touchpoint Tracking**
   Record all interactions: emails, calls, SMS, meetings, video calls, social media, and physical mail.

**Outreach Campaigns**
   Automated multi-step sequences with email and SMS support. Configurable delays, skip-if-responded logic, and rate limiting.

**Marketing Documents**
   Manage brochures, case studies, pricing sheets, proposals, and presentations with usage tracking.

**Seller Profiles**
   Internal seller profiles with working hours, timezone support, auto-assignment, and performance stats.

**REST API**
   Full Django REST Framework API for all models with filtering, search, and nested endpoints.

**Flexible Architecture**
   - Works with any user model
   - Optional Celery integration for async tasks
   - Pluggable SMS backends (Twilio, console)
   - Pluggable email backends

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   quickstart
   configuration
   models
   api

Quick Start
-----------

Install the package:

.. code-block:: bash

   pip install django-acquisitions

Add to your Django settings:

.. code-block:: python

   INSTALLED_APPS = [
       ...
       'acquisitions',
   ]

Run migrations:

.. code-block:: bash

   python manage.py migrate acquisitions

Create your first prospective client:

.. code-block:: python

   from acquisitions.models import ProspectiveClient

   pc = ProspectiveClient.objects.create(
       company_name="Acme Corp",
       status=ProspectiveClient.Status.NEW,
       source=ProspectiveClient.Source.WEBSITE,
   )

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
