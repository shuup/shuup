Setting up the Shoop REST API
=============================


First, add ``rest_framework`` and ``shoop.api`` to your ``INSTALLED_APPS``.

Then -- and this differs from Django REST Framework's defaults -- you *must* add
the ``REST_FRAMEWORK`` configuration dict to your settings.  Django REST Framework
defaults to no permission checking whatsoever (``rest_framework.permissions.AllowAny``),
which would make all of your data world-readable and writable.

This is not what we want to accidentally happen, so configuration is enforced.

For the sake of demonstration, let's make the API only accessible for superusers with
the ``IsAdminUser`` permission policy.  (Authentication is enabled by the default settings.)

.. code-block:: python

   REST_FRAMEWORK = {
       'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.IsAdminUser',)
   }


Now just add the API to your root urlconf.

.. code-block:: python

   urlpatterns = patterns(
       # *snip*
       url(r'^api/', include('shoop.api.urls')),
       # *snip*
   )


All done! If you visit the `/api/` URL (as a suitably authenticated user), you should be
presented with Django REST Framework's human-friendly user interface.
