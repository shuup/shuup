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

Provide Categories
------------------

``admin_category_form_part``
    Additional ``FormPart`` classes for Category editing.
``admin_contact_form_part``
    Additional ``FormPart`` classes for Contact editing.
``admin_product_form_part``
    Additional ``FormPart`` classes for Product editing.
    (This is used by pricing modules, for instance.)
``admin_module``
    Admin module classes. Practically all of the functionality in the admin is built
    via admin modules.
``front_template_helper_namespace``
    Additional namespaces to install in the ``shoop`` "package" within
    template contexts.
    .. seealso:: :ref:`custom-template-helper-functions`
``front_urls``
    Lists of frontend URLs to be appended to the usual frontend URLs.
``front_urls_post``
    Lists of frontend URLs to be appended to the usual frontend URLs, even after ``front_urls``.
    Most of the time, ``front_urls`` should do.
``front_urls_pre``
    Lists of frontend URLs to be prepended to the usual frontend URLs.
    Most of the time, ``front_urls`` should do.
``notify_action``
    Notification framework :py:class:`~shoop.notify.Action` classes.
``notify_condition``
    Notification framework :py:class:`~shoop.notify.Condition` classes.
``notify_event``
    Notification framework :py:class:`~shoop.notify.Event` classes.
``payment_method_module``
    Payment method module classes (deriving from :py:class:`shoop.core.methods.base.BasePaymentMethodModule`),
    as used by :py:class:`shoop.core.models.PaymentMethod`.
``pricing_module``
    Pricing module classes; the pricing module in use is set with the ``SHOOP_PRICING_MODULE`` setting.
``shipping_method_module``
    Shipping method module classes (deriving from :py:class:`shoop.core.methods.base.BaseShippingMethodModule`),
    as used by :py:class:`shoop.core.models.ShippingMethod`.
``supplier_module``
    Supplier module classes (deriving from :py:class:`shoop.core.suppliers.base.BaseSupplierModule`),
    as used by :py:class:`shoop.core.models.Supplier`.
``tax_module``
    Tax module classes; the tax module in use is set with the ``SHOOP_TAX_MODULE`` setting.
``xtheme``
    XTheme themes (full theme sets).
``xtheme_plugin``
    XTheme plugins (that are placed into placeholders within themes).
``xtheme_resource_injection``
    XTheme resources injection function that takes current context and content as parameters.
