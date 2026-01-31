Installation
============

Requirements
------------

* Python 3.10+
* Django 4.2+

Basic Installation
------------------

Install using pip:

.. code-block:: bash

   pip install django-acquisitions

Optional Dependencies
---------------------

For Celery task support:

.. code-block:: bash

   pip install django-acquisitions[celery]

For Twilio SMS support:

.. code-block:: bash

   pip install django-acquisitions[twilio]

For Django REST Framework API:

.. code-block:: bash

   pip install django-acquisitions[drf]

Or install all optional dependencies:

.. code-block:: bash

   pip install django-acquisitions[all]

Development Installation
------------------------

Clone the repository and install in development mode:

.. code-block:: bash

   git clone https://github.com/specialorange/django-acquisitions.git
   cd django-acquisitions
   pip install -e ".[all]"
