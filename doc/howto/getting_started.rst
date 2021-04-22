Installing Shuup
================

.. note::

   If you are planning on developing Shuup,
   read the :doc:`Getting Started with Shuup Development guide
   <getting_started_dev>` instead.

Requirements
------------

* Python 3.6+. https://www.python.org/download/.
* Django's minimum supported version is 2.2 LTS.
* Any database supported by Django. https://docs.djangoproject.com/en/3.0/ref/databases/ .

Installation
------------

Docker
######

Fastest way to get Shuup up and running is to use `Docker <https://www.docker.com>`_.

1. Run:

   .. code-block:: shell

      docker-compose up

2. Open `localhost:8000/sa <http://localhost:8000/sa>`_ in a browser,
   log in with username: ``admin`` password: ``admin``

Locally
#######

This guide assumes familiarity with the PyPA tools for Python packaging,
including ``pip`` and ``virtualenv``.

1. Update pip and setuptools

   .. code-block:: shell

      pip install -U pip
      pip install -U setuptools

2. Set up a new virtualenv for Shuup and activate it

   .. code-block:: shell

      virtualenv shuup-venv
      . shuup-venv/bin/activate

3. Install shuup via pypi

   .. code-block:: shell

      pip install shuup

4. Once installed, you can begin setting up a Django project using whichever
   standards you fancy. Refer to the top-level `settings
   <https://github.com/shuup/shuup/blob/master/shuup_workbench/settings/base_settings.py>`_
   and `urls
   <https://github.com/shuup/shuup/blob/master/shuup_workbench/urls.py>`_
   for configuration details. At minimum, you will need to add ``shuup.core``
   to your ``INSTALLED_APPS``.

.. note::
   Shuup uses ``django-parler`` for model translations. Please ensure
   ``PARLER_DEFAULT_LANGUAGE_CODE`` is set. See `django-parler configuration
   <http://django-parler.readthedocs.io/en/latest/configuration.html>`_ for more
   details.

.. note::
   Shuup uses the ``LANGUAGES`` setting to render multilingual forms. You'll likely
   want to override this setting to restrict your applications supported languages.

5. Once you have configured the Shuup apps you would like to use, run the
   following commands to create the database and initialize Shuup

   .. code-block:: shell

      python manage.py migrate
      python manage.py shuup_init


.. note::
    Some extra steps is required for **Windows**

    If you want to install all requirements just with pip, you have to install MS
    Visual C++ Build Tools as explained in `Python’s wiki
    <https://wiki.python.org/moin/WindowsCompilers>`__. This way
    everything will be build automatically on your Windows machine, alternatively
    you may install failed to build packages from https://www.lfd.uci.edu/~gohlke/pythonlibs/.

    If you have OSError: dlopen() failed to load a library: cairo / cairo-2 error,
    please carefully follow these `instructions
    <https://weasyprint.readthedocs.io/en/latest/install.html#windows>`__.

    If you still have the same error, be sure that your installed python and GTK run
    time has the same 32 or 64 bit. It's important.

    Error is still there? Try to edit Windows environment PATH, and move GTK Runtime
    location to the top of the list.


Shuup Packages
--------------

Shuup is a constellation of Django apps, with many delivered in the single
"Shuup Base" distribution, and with additional apps available as separate
downloads.

``shuup.core`` is the core package required by all Shuup installations.
It contains the core business logic for e-commerce, and all of the database
models required. However, it contains no frontend or admin dashboard, as
different projects may wish to replace them with other components or even
elide them altogether.

``shuup.front`` is a basic but fully featured storefront. It itself has
several sub-applications that may be used to toggle functionality on and off.

* ``shuup.front.apps.auth`` is a wrapper around django auth for login and
  password recovery.
* ``shuup.front.apps.registration`` provides views for customer activation
  and registration.
* ``shuup.front.apps.customer_information`` provides views for customer
  address management.
* ``shuup.front.apps.personal_order_history`` adds views for customer
  order history.
*  ``shuup.front.apps.simple_order_notification`` can be used to send
   email notifications to the customer upon order completion.
* ``shuup.front.apps.simple_search`` provides basic product search
  functionality.
* ``shuup.front.apps.recently_viewed_products`` can be used to display the last
  five products viewed by the customer.

``shuup.admin`` provides a fully featured administration dashboard.

``shuup.addons`` can be used to install and manage Shuup addons.

``shuup.campaigns`` provides a highly customizable promotion and discount
management system.

``shuup.customer_group_pricing`` can be used to customize product pricing by
customer contact groups.

``shuup.default_tax`` is a rules-based tax module that calculates and applies
taxes on orders. See the :doc:`prices and taxes documentation
<../ref/prices_and_taxes>` for details.

``shuup.guide`` integrates search results from this documentation into Admin
search.

``shuup.notify`` is a generic notification framework that can be used to
inform users about various events (order creation, shipments, password
resets, etc). See the :doc:`notification documentation
<../ref/notify_specification>` for details.

``shuup.order_printouts`` adds support to create PDF printouts of orders from
admin.

``shuup.simple_cms`` is a basic content management system that can be used to
add pages to the storefront.

``shuup.simple_supplier`` is a simple inventory management system that can be
used to keep track of product inventory.
