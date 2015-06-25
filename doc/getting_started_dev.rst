Getting Started with Shoop Development
======================================

.. note::

   If you are planning on using Shoop for developing your own shop,
   read the :doc:`other Getting Started guide <getting_started>` instead.

Installation for Development
----------------------------

To install Shoop for developing, setup a virtualenv and activate it,
then run the following command in the root of the checkout:

.. code-block:: shell

   pip install -e .[testing]

If you don't need the testing dependencies, drop the ``[testing]`` suffix.
Note: Some tests might need even more dependencies, then try
``[everything]`` suffix.

.. note::

   If you get the following error::

     --editable=.[testing] should be formatted with svn+URL, ...

   you should upgrade your pip:

   .. code-block:: shell

      pip install -U pip

Workbench, the built-in test project
------------------------------------

The Workbench project in the repository is a self-contained Django
project set up to use an SQLite database. It is used by the test suite
and is also useful for development on its own.

Practically the only difference to a normal Django project is that instead
of ``python manage.py``, one uses ``python -m shoop_workbench``.

To get started with Workbench, invoke the following in the Shoop working copy
root.

.. code-block:: shell

   # Migrate database.
   python -m shoop_workbench migrate

   # Import some basic data.
   python -m shoop_workbench shoop_populate_mock --with-superuser=admin

   # Run the Django development server (on port 8000 by default).
   python -m shoop_workbench runserver

You can use the credentials ``admin``/``admin``, that is username ``admin``
and password ``admin`` to log in as a superuser on http://127.0.0.1:8000/ .

Building resources
------------------

Shoop uses JavaScript and CSS resources that are compiled using various
Node.js packages.  These resources are compiled automatically by
``setup.py`` when installing Shoop with pip, but if you make changes to
the source files (e.g. under ``shoop/admin/static_src``), the resources
have to be rebuilt.

This can be done with

.. code-block:: shell

   python setup.py build_resources

The command also accepts couple arguments, see its help for more details:

.. code-block:: shell

   python setup.py build_resources --help

Running tests
-------------

To run tests in the active virtualenv:

.. code-block:: shell

   py.test -v shoop_tests
   # Or with coverage
   py.test -vvv --cov shoop --cov-report html shoop_tests

To run tests for all supported Python versions run:

.. code-block:: shell

   pip install tox  # To install tox, needed just once
   tox

Docstring coverage
------------------

The DocCov script is included for calculating some documentation coverage metrics.

.. code-block:: shell

   python _misc/doccov.py shoop/core -o doccov.html
