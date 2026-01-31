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


Prospective Clients (Leads)
---------------------------

List and create prospective clients:

.. code-block:: http

   GET /api/acquisitions/leads/
   POST /api/acquisitions/leads/

Retrieve, update, or delete a prospective client:

.. code-block:: http

   GET /api/acquisitions/leads/{uuid}/
   PUT /api/acquisitions/leads/{uuid}/
   PATCH /api/acquisitions/leads/{uuid}/
   DELETE /api/acquisitions/leads/{uuid}/

**Filtering:**

- ``?status=new`` - Filter by status
- ``?assigned_to=me`` - Filter by current user
- ``?search=acme`` - Search by company name

**Actions:**

Convert to customer:

.. code-block:: http

   POST /api/acquisitions/leads/{uuid}/convert/

Enroll in campaign:

.. code-block:: http

   POST /api/acquisitions/leads/{uuid}/enroll_campaign/
   Content-Type: application/json

   {"campaign_uuid": "..."}


Contacts
--------

Nested under prospective clients:

.. code-block:: http

   GET /api/acquisitions/leads/{uuid}/contacts/
   POST /api/acquisitions/leads/{uuid}/contacts/
   GET /api/acquisitions/leads/{uuid}/contacts/{contact_uuid}/
   PUT /api/acquisitions/leads/{uuid}/contacts/{contact_uuid}/
   PATCH /api/acquisitions/leads/{uuid}/contacts/{contact_uuid}/
   DELETE /api/acquisitions/leads/{uuid}/contacts/{contact_uuid}/


Touchpoints
-----------

Nested under prospective clients:

.. code-block:: http

   GET /api/acquisitions/leads/{uuid}/touchpoints/
   POST /api/acquisitions/leads/{uuid}/touchpoints/
   GET /api/acquisitions/leads/{uuid}/touchpoints/{touchpoint_uuid}/

**Example: Create a touchpoint**

.. code-block:: http

   POST /api/acquisitions/leads/{uuid}/touchpoints/
   Content-Type: application/json

   {
       "touchpoint_type": "email",
       "direction": "outbound",
       "subject": "Follow up",
       "occurred_at": "2024-01-15T10:00:00Z"
   }


Campaigns
---------

.. code-block:: http

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

.. code-block:: http

   GET /api/acquisitions/documents/
   POST /api/acquisitions/documents/
   GET /api/acquisitions/documents/{uuid}/

**Filtering:**

- ``?type=brochure`` - Filter by document type

**Actions:**

Track views and downloads:

.. code-block:: http

   POST /api/acquisitions/documents/{uuid}/track_view/
   POST /api/acquisitions/documents/{uuid}/track_download/

.. note::

   Non-staff users cannot see documents marked as ``is_internal_only=True``.


Seller Profiles
---------------

Get current user's profile:

.. code-block:: http

   GET /api/acquisitions/sellers/me/

List all sellers (requires seller profile or staff):

.. code-block:: http

   GET /api/acquisitions/sellers/


Industries
----------

.. code-block:: http

   GET /api/acquisitions/industries/
   POST /api/acquisitions/industries/
   GET /api/acquisitions/industries/{id}/


Categories
----------

.. code-block:: http

   GET /api/acquisitions/categories/
   POST /api/acquisitions/categories/
   GET /api/acquisitions/categories/{id}/
