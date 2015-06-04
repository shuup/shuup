The Provides system
===================

The Provides system is Shoop's mechanism for discovering and loading
components, both first-party and third-party.  Shoop apps use
the provides system in various ways.

* The core itself uses Provides for discovering method and supplier modules.
* ``shoop.admin`` uses Provides to load admin modules, form customizations etc.
* ``shoop.front`` uses it for URLconf overrides etc.

.. TODO:: Document the various ways better.

Provides are grouped under different categories, such as ``admin_module``,
``shipping_method_module``, ``front_urls``, etc.

Declaring Provides
------------------

Shoop uses the Django 1.7+ ``AppConfig`` system to declare provides.

Quite simply, a developer needs only include a dict with provide categories as
the keys and lists of loading specs as values for new provides to be discovered.

.. code-block:: python

   class PigeonAppConfig(AppConfig):

       provides = {
           "shipping_method_module": [
               "pigeon.module:PigeonShippingModule"
           ]
       }

.. note:: Some provides also require the class named by the spec string to include
          an ``identifier`` field. Refer to the implementation guides for particular
          functionalities for details.

Using Provides
--------------

Provide management functions are found in the :mod:`shoop.apps.provides` module.

In general, the :obj:`shoop.apps.provides.get_provide_objects` method is your most useful
entry point.
