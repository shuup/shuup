Shuup Web APIs
==============

REST API
--------

Shuup has a powerful API to enable users to access and modify data through endpoints. Users can create several applications to
consume the API, from mobile applications to virtual reality devices and whatever platform capable of making HTTP requests.

The Shuup REST API is built on `Django REST Framework`_ with additional
functionality built on :doc:`ref/provides` to auto-discover available API endpoints.


.. toctree::
   :glob:
   :maxdepth: 2

   web_api/rest_setup
   web_api/rest_documentation
   web_api/rest_permissions
   web_api/rest_usage

.. _Django REST Framework: http://www.django-rest-framework.org/
