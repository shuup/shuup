Addons
======

Shuup contains facilities for installing, detecting, loading and configuring
additional functionality with little or no system administration knowledge
needed.  Packages that can be loaded in this way are called Addons.  Addons
aren't very special, though: under the surface they are nothing more than
standard Django applications that are discovered using the `Setuptools Entry
Points mechanism <entrypoints_>`_.  Functionality registration after this
occurs via the Shuup :doc:`Provides <../ref/provides>` subsystem.

Configuring your project to load addons
---------------------------------------

The Shuup addon manager handles adding addons into Django's ``INSTALLED_APPS``
list during project initialization time.

It's easy to convert a standard Django configuration to be addons enabled.

For instance, take a bare-bones Shuup core installation.

.. code-block:: python

    INSTALLED_APPS = (
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',
        'shuup.core',
        'shuup.customer_group_pricing',
        'shuup.simple_supplier',
        'shuup.default_tax',
        'shuup.admin',
    )

The management interface for the addon loader requires one additional
configuration key, ``SHUUP_ENABLED_ADDONS_FILE``, to name a path to a
configuration file that is writable by the application server.

The ``shuup.addons.add_enabled_addons()`` method manages reading this file,
cross-referencing them with the entry points published by Setuptools and
adding them into the installed apps list.

Putting this all together,

.. code-block:: python

    from shuup.addons import add_enabled_addons

    # *snip*

    # This varies depending on how your particular project arranges writable files.
    SHUUP_ENABLED_ADDONS_FILE = os.path.join(BASE_DIR, "enabled_addons")

    INSTALLED_APPS = add_enabled_addons(SHUUP_ENABLED_ADDONS_FILE, (
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',
        'shuup.core',
        'shuup.customer_group_pricing',
        'shuup.simple_supplier',
        'shuup.default_tax',
        'shuup.admin',
        'shuup.addons',
    ))

    # *snip*

will enable your project to load Shuup addons.

Installing and configuring addons
---------------------------------

Once ``shuup.addons`` is in your ``INSTALLED_APPS`` list, a section for
managing addons appears in the administration panel.

Developing addons
-----------------

As discussed before, addons are simply Django applications with a Setuptools
``entry_points`` stanza in ``setup.py``.

This means addon development doesn't require any special steps; just adding
the new application to a test project's (such as Workbench's)
``INSTALLED_APPS`` is enough to get you running.

Preparing addons for distribution
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When the time comes to actually distribute your new addon, `configure your
package according to the PyPUG guidelines <pypug-dist_>`_ and within the
``entry_points`` section add a ``shuup.addon`` entry point stanza, such as
this (example taken from the `shuup-stripe <https://github.com/shuup/shuup-stripe>`_
addon):

.. code-block:: python

    setuptools.setup(
        # ...
        entry_points={"shuup.addon": "shuup_stripe=shuup_stripe"}
    )


.. note::

   It's recommended you follow the ``name=name`` format for the entry point
   definition. Further iterations of addon discovery may change the format.

With this in your ``setup.py``, you can now

* Use ``python setup.py sdist`` to create a source distribution for your addon
  and install it via the administration panel as you would for any old addon.
* Or run ``pip install -e .`` to install the addon in your shop's
  virtualenv in `editable mode <editable_>`_, then enable the addon via the
  administration panel.

(If you had manually added the application into your ``INSTALLED_APPS`` as
discussed before, this would be a good time to take it out of there, as
otherwise Django will complain about duplicates.)

.. _pypug-dist: https://packaging.python.org/en/latest/distributing.html
.. _entrypoints: https://pythonhosted.org/setuptools/pkg_resources.html#entry-points
.. _editable: https://pip.pypa.io/en/latest/reference/pip_install.html#editable-installs
