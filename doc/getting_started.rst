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

      pip install /stuff/shoop

This will install Shoop and its dependencies into your virtualenv.

After this, you can begin setting up a Django project using whichever
standards you fancy.

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
