Getting Started with Shuup Development
======================================

.. note::

   If you are planning on using Shuup to build your own shop,
   read the :doc:`Getting Started with Shuup guide <getting_started>`
   instead.

.. note::

   Interested in contributing to Shuup? Take a look at our `Contribution
   Guide <https://www.shuup.com/en/shuup/contribution-guide>`__.

Requirements
------------
* Python 3.6+. https://www.python.org/download/.
* Node.js (v12 or above). https://nodejs.org/en/download/
* Any database supported by Django.

Installation for Shuup Development
----------------------------------

To start developing Shuup, you'll need a Git checkout of Shuup and a
Github fork of Shuup for creating pull requests.  Github pull requests
are used to get your changes into Shuup Base.

If you haven't done so already, create a fork of Shuup in Github by
clicking the "Fork" button at https://github.com/shuup/shuup and
clone the fork to your computer as usual. See `Github Help about
forking repos <https://help.github.com/articles/fork-a-repo/>`__ for
details.

Docker
######

Fastest way to get Shuup development environment up and running is to use `Docker <https://www.docker.com>`_.

1. Run the development compose file, it allows your local changes to update in the browser:

   .. code-block:: shell

      docker-compose -f docker-compose-dev.yml up

2. Open `localhost:8000/sa <http://localhost:8000/sa>`_ in a browser,
   log in with username: ``admin`` password: ``admin``

Locally
#######

1. Setup a virtualenv and activate it. See `Virtualenv User Guide
   <https://virtualenv.pypa.io/en/latest/userguide.html>`__, if you
   are unfamiliar with virtualenv.  For example, following commands
   create and activate a virtualenv in Linux:

   .. code-block:: shell

     virtualenv shuup-venv
      . shuup-venv/bin/activate

3. Finally, you'll need to install Shuup in the activated virtualenv.
   To do that, run the following commands in the
   root of the checkout (within the activated virtualenv):

   .. code-block:: shell

      pip install -r requirements-dev.txt

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

.. note::
    Extra information/warning regarding SQLite `read more
    <https://github.com/shuup/shuup/issues/1730>`__.


Workbench, the built-in test project
------------------------------------

The Workbench project in the repository is a self-contained Django
project set up to use an SQLite database. It is used by the test suite
and is also useful for development on its own.

Practically the only difference to a normal Django project is that instead
of ``python manage.py``, one uses ``python -m shuup_workbench``.

To get started with Workbench, invoke the following in the Shuup working copy
root.

.. code-block:: shell

   # Migrate database.
   python -m shuup_workbench migrate

   # Import some basic data.
   python -m shuup_workbench shuup_init

   # Create superuser so you can login admin panel
   python -m shuup_workbench createsuperuser

   # Run the Django development server (on port 8000 by default).
   python -m shuup_workbench runserver

You can use the created credentials to log in as a superuser on
http://127.0.0.1:8000/sa/ .

Building resources
------------------

Shuup uses JavaScript and CSS resources that are compiled using various
Node.js packages.  These resources are compiled automatically by
``setup.py`` when installing Shuup with pip, but if you make changes to
the source files (e.g. under ``shuup/admin/static_src``), the resources
have to be rebuilt.

This can be done with

.. code-block:: shell

   python setup.py build_resources

The command also accepts couple arguments, see its help for more details:

.. code-block:: shell

   python setup.py build_resources --help

.. note::
    Make sure your running rather new version from `Node
    <https://nodejs.org/en/>`__ and non LTS version is recommended
    for advanced users only.


Running tests
-------------

To run tests in the active virtualenv:

.. code-block:: shell
   pip install -r requirements-tests.txt

   py.test -v --nomigrations shuup_tests
   # Or with coverage
   py.test -vvv --nomigrations --cov shuup --cov-report html shuup_tests

Running browser tests
---------------------

.. code-block:: shell

   SHUUP_BROWSER_TESTS=1 py.test -v --nomigrations shuup_tests/browser

For Chrome

.. code-block:: shell

   SHUUP_BROWSER_TESTS=1 py.test -v --nomigrations --splinter-webdriver=chrome shuup_tests/browser

For OSX with Homebrew:

.. code-block:: shell

    # Install Chrome driver (tested with 2.34.522932 (4140ab217e1ca1bec0c4b4d1b148f3361eb3a03e))
    brew install chromedriver

    # Install Geckodriver (for Firefox)
    brew install geckodriver

    # If your current version is below 0.29.1 (for Firefox)
    brew upgrade geckodriver

    # Make sure the selenium is up to date (tested with 3.141.0)
    pip install selenium -U

    # Make sure splinter is up to date (tested with 0.14.0)
    pip install splinter -U

For other OS and browsers check package documentation directly:
* `Geckodriver <https://github.com/mozilla/geckodriver>`__
* `Selenium <https://github.com/SeleniumHQ/selenium>`__
* `Splinter <https://github.com/cobrateam/splinter>`__

Warning! There is inconsistency issues with browser tests and if you suspect your
changes did not break the tests we suggest you rerun the test before
starting debugging more.

Known issues:
* With Chrome test `shuup_tests/browser/front/test_checkout_with_login_and_register.py`
is very unstable.

Collecting translatable messages
--------------------------------

To update the PO catalog files which contain translatable (and
translated) messages, issue ``shuup_makemessages`` management command in
the ``shuup`` directory:

.. code-block:: shell

   cd shuup && python -m shuup_workbench shuup_makemessages
