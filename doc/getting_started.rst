Getting Started with Shoop
==========================

.. note::

   If you are planning on developing Shoop,
   read the :doc:`other Getting Started guide <getting_started_dev>` instead.

Installation
------------

.. TODO:: Update this when Shoop is published to PyPI.

This guide assumes familiarity with the PyPA tools for Python packaging,
including ``pip`` and ``virtualenv``.

1. Set up a new virtualenv for your Shoop project.
2. Grab a Git clone of the Shoop sources. For this guide,
   we'll assume the checkout of the clone lives in :file:`/stuff/shoop`.
3. Activate the virtualenv. Within the virtualenv, run

   .. code-block:: shell

      pip install -e /stuff/shoop

This will install Shoop and its dependencies into your virtualenv.

After this, you can begin setting up a Django project using whichever
standards you fancy.

.. TODO:: Mention ``npm run build`` somehow...


Quickstart: Adding Shoop to a new project
-----------------------------------------

**Installed apps**

Shoop requires several third-party apps to be added to ``INSTALLED_APPS``,
depending on installed shoop packages. To get a shop up and running, add
some Shoop and dependent apps in your settings.

   .. code-block:: python

      "shoop.core",
      "shoop.admin",
      "shoop.front",
      "easy_thumbnails",
      "filer",
      "django_jinja",

**Template engines**

Shoop apps use Jinja templating and this should be added to the template
engines *before* the default django template engine. Add to your
``TEMPLATES`` something like the following:

   .. code-block:: python

      {
         "BACKEND": "django_jinja.backend.Jinja2",
         "APP_DIRS": True,
         "OPTIONS": {
            "match_extension": ".jinja",
         }
      },

See `django-jinja documentation <http://niwinz.github.io/django-jinja/#_user_guide_for_django_1_8>`__
for more options.

**Url configuration**

Include the Shoop urls in your project, for example as follows:

   .. code-block:: python

      url(r'^sa/', include('shoop.admin.urls', namespace="shoop_admin", app_name="shoop_admin")),
      url(r'^', include('shoop.front.urls', namespace="shoop", app_name="shoop")),

**Build assets**

You need to build assets Shoop uses in the admin for example. Go to
wherever Shoop is installed to (ie ``/stuff/shoop``) and do the following:

   .. code-block:: shell

      python build-all.py

**Start the app**

Do your normal ``syncdb`` and other required Django project setup stuff here
and after that you should be able to ``runserver`` and then navigating the
root should show you the Shoop admin dashboard.

Shoop Packages
--------------

Shoop is a constellation of Django apps, with many delivered in the single
"Shoop Base" distribution, and with additional apps available as separate
downloads.

The core package all Shoop installations will require is ``shoop.core``.
It contains the core business logic for e-commerce, and all of the database
models required. However, it contains no frontend or admin dashboard, as
different projects may wish to replace them with other components or even
elide them altogether.

A default frontend, a basic but fully featured storefront, is included, as
the application ``shoop.front``. It itself has several sub-applications that
may be used to toggle functionality on and off.

.. TODO:: Describe the sub-apps.

A fully featured administration dashboard is also included as the application
``shoop.admin``.
