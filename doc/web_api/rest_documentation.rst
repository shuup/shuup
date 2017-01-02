API Documentation
=================

As the API is built with Django REST Framework (DRF), you can visit the ``/api/`` URL to access the browseable API using the default
DRF interface, but only if ``rest_framework.renderers.BrowsableAPIRenderer`` is in the ``DEFAULT_RENDERER_CLASSES`` setting, which is the default.

Alongside with the default browseable API, we can see the complete API documentation with URLs, methods and parameters
on-the-fly using `Django REST Swagger`_. You can access the interactive API documentation at your development
server or even at a production one.

To see that, just make sure the application ``rest_framework_swagger`` is in your ``INSTALLED_APPS``.

Visit the ``/api/docs/`` URL on your browser and it is done. You should see the available APIs endpoints, their descriptions,
methods and parameters.

See also :doc:`rest_permissions` to configure the access level of your API documentation.

.. _Django REST Swagger: https://github.com/marcgibbons/django-rest-Swagger
