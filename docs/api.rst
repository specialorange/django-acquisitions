REST API
========

django-acquisitions provides a REST API built with Django REST Framework.

Setup
-----

Install with the DRF optional dependency:

.. code-block:: bash

   pip install django-acquisitions[drf]

Add the URLs to your project:

.. code-block:: python

   urlpatterns = [
       ...
       path('api/acquisitions/', include('acquisitions.api.urls')),
   ]


Authentication
--------------

All endpoints require authentication. The API uses DRF's standard authentication classes.


Prospective Clients
-------------------

List and create prospective clients:

.. code-block:: text

   GET /api/acquisitions/prospective-clients/
   POST /api/acquisitions/prospective-clients/

Retrieve, update, or delete a prospective client:

.. code-block:: text

   GET /api/acquisitions/prospective-clients/{uuid}/
   PUT /api/acquisitions/prospective-clients/{uuid}/
   PATCH /api/acquisitions/prospective-clients/{uuid}/
   DELETE /api/acquisitions/prospective-clients/{uuid}/

**Filtering:**

- ``?status=new`` - Filter by status
- ``?assigned_to=me`` - Filter by current user
- ``?search=acme`` - Search by company name

**Actions:**

Convert to customer:

.. code-block:: text

   POST /api/acquisitions/prospective-clients/{uuid}/convert/

Enroll in campaign:

.. code-block:: text

   POST /api/acquisitions/prospective-clients/{uuid}/enroll_campaign/

   {"campaign_uuid": "..."}


Contacts
--------

Nested under prospective clients:

.. code-block:: text

   GET /api/acquisitions/prospective-clients/{uuid}/contacts/
   POST /api/acquisitions/prospective-clients/{uuid}/contacts/
   GET /api/acquisitions/prospective-clients/{uuid}/contacts/{contact_uuid}/
   PUT /api/acquisitions/prospective-clients/{uuid}/contacts/{contact_uuid}/
   PATCH /api/acquisitions/prospective-clients/{uuid}/contacts/{contact_uuid}/
   DELETE /api/acquisitions/prospective-clients/{uuid}/contacts/{contact_uuid}/


Touchpoints
-----------

Nested under prospective clients:

.. code-block:: text

   GET /api/acquisitions/prospective-clients/{uuid}/touchpoints/
   POST /api/acquisitions/prospective-clients/{uuid}/touchpoints/
   GET /api/acquisitions/prospective-clients/{uuid}/touchpoints/{touchpoint_uuid}/

**Example: Create a touchpoint**

.. code-block:: json

   {
       "touchpoint_type": "email",
       "direction": "outbound",
       "subject": "Follow up",
       "occurred_at": "2024-01-15T10:00:00Z"
   }


Dashboard
---------

Team overview and analytics:

.. code-block:: text

   GET /api/acquisitions/dashboard/

Returns full dashboard data including:

- Pipeline summary (counts by status)
- Stale prospects (no recent contact)
- Unassigned prospects
- Seller performance
- Upcoming outreach
- Conversion funnel
- Campaign performance

**Query Parameters:**

- ``?stale_days=14`` - Days without contact to be considered stale
- ``?activity_days=30`` - Days to look back for activity metrics

**Individual endpoints:**

.. code-block:: text

   GET /api/acquisitions/dashboard/pipeline/
   GET /api/acquisitions/dashboard/stale/
   GET /api/acquisitions/dashboard/unassigned/
   GET /api/acquisitions/dashboard/sellers/
   GET /api/acquisitions/dashboard/funnel/
   GET /api/acquisitions/dashboard/campaigns/
   GET /api/acquisitions/dashboard/activity/


Campaigns
---------

.. code-block:: text

   GET /api/acquisitions/campaigns/
   POST /api/acquisitions/campaigns/
   GET /api/acquisitions/campaigns/{uuid}/
   PUT /api/acquisitions/campaigns/{uuid}/
   PATCH /api/acquisitions/campaigns/{uuid}/
   DELETE /api/acquisitions/campaigns/{uuid}/

Campaign detail includes nested steps:

.. code-block:: json

   {
       "uuid": "...",
       "name": "Welcome Series",
       "status": "active",
       "steps": [
           {
               "step_order": 0,
               "step_type": "email",
               "delay_days": 0,
               "subject_template": "Welcome!"
           }
       ]
   }


Marketing Documents
-------------------

.. code-block:: text

   GET /api/acquisitions/documents/
   POST /api/acquisitions/documents/
   GET /api/acquisitions/documents/{uuid}/

**Filtering:**

- ``?type=brochure`` - Filter by document type

**Actions:**

Track views and downloads:

.. code-block:: text

   POST /api/acquisitions/documents/{uuid}/track_view/
   POST /api/acquisitions/documents/{uuid}/track_download/

.. note::

   Non-staff users cannot see documents marked as ``is_internal_only=True``.


Seller Profiles
---------------

Get current user's profile:

.. code-block:: text

   GET /api/acquisitions/sellers/me/

List all sellers (requires seller profile or staff):

.. code-block:: text

   GET /api/acquisitions/sellers/


Industries
----------

.. code-block:: text

   GET /api/acquisitions/industries/
   POST /api/acquisitions/industries/
   GET /api/acquisitions/industries/{id}/


Categories
----------

.. code-block:: text

   GET /api/acquisitions/categories/
   POST /api/acquisitions/categories/
   GET /api/acquisitions/categories/{id}/
