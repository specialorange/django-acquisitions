Configuration
=============

django-acquisitions can be configured through Django settings.

Settings
--------

Add these to your Django ``settings.py``:

.. code-block:: python

   ACQUISITIONS = {
       # SMS backend configuration
       'SMS_BACKEND': 'acquisitions.backends.sms.console.ConsoleSMSBackend',

       # Email backend (uses Django's email backend by default)
       'EMAIL_BACKEND': 'acquisitions.backends.email.django_email.DjangoEmailBackend',
   }

SMS Backends
------------

Console Backend (Development)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Prints SMS messages to the console:

.. code-block:: python

   ACQUISITIONS = {
       'SMS_BACKEND': 'acquisitions.backends.sms.console.ConsoleSMSBackend',
   }

Twilio Backend (Production)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Sends SMS via Twilio:

.. code-block:: python

   ACQUISITIONS = {
       'SMS_BACKEND': 'acquisitions.backends.sms.twilio.TwilioSMSBackend',
   }

   # Twilio credentials
   TWILIO_ACCOUNT_SID = 'your-account-sid'
   TWILIO_AUTH_TOKEN = 'your-auth-token'
   TWILIO_PHONE_NUMBER = '+1234567890'

Celery Configuration
--------------------

For async task processing, configure Celery:

.. code-block:: python

   # celery.py
   from celery import Celery

   app = Celery('your_project')
   app.config_from_object('django.conf:settings', namespace='CELERY')
   app.autodiscover_tasks()
