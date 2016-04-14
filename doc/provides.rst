The Provides system
===================

The Provides system is Shoop's mechanism for discovering and loading
components, both first-party and third-party.  Shoop apps use
the provides system in various ways.

* The core itself uses Provides for discovering method and supplier modules.
* ``shoop.admin`` uses Provides to load admin modules, form customizations etc.
* ``shoop.front`` uses it for URLconf overrides etc.

The provide categories used by Shoop are listed in :ref:`provide-categories` but you
can also define your own categories as you wish.

.. TODO:: Document the various ways better.

Provides are grouped under different categories, such as ``admin_module``,
``xtheme_plugin``, ``front_urls``, etc.

Declaring Provides
------------------

Shoop uses the Django 1.7+ ``AppConfig`` system to declare provides.

Quite simply, a developer needs only include a dict with provide categories as
the keys and lists of loading specs as values for new provides to be discovered.

.. code-block:: python

   class PigeonAppConfig(AppConfig):

       provides = {
           'service_provider_admin_form': [
               'pigeon.admin_forms:PigeonShippingAdminForm',
           ],
       }

.. note:: Some provides also require the class named by the spec string to include
          an ``identifier`` field. Refer to the implementation guides for particular
          functionalities for details.

Using Provides
--------------

Provide management functions are found in the :mod:`shoop.apps.provides` module.

In general, the :obj:`shoop.apps.provides.get_provide_objects` method is your most useful
entry point.

.. _provide-categories:

Provide Categories
------------------

Core
~~~~

``admin_category_form_part``
    Additional ``FormPart`` classes for Category editing.

``admin_contact_form_part``
    Additional ``FormPart`` classes for Contact editing.

``admin_product_form_part``
    Additional ``FormPart`` classes for Product editing.
    (This is used by pricing modules, for instance.)

``admin_shop_form_part``
    Additional ``FormPart`` classes for Shop editing.

``admin_module``
    Admin module classes. Practically all of the functionality in the admin is built
    via admin modules.

``discount_module``
    `~shoop.core.pricing.DiscountModule` for pricing system.

``front_template_helper_namespace``
    Additional namespaces to install in the ``shoop`` "package" within
    template contexts.
    .. seealso:: :ref:`custom-template-helper-functions`

``admin_order_toolbar_button``
    Additional ``BaseActionButton`` subclasses for Order detail.
    Subclass init should take current order as a parameter.

``front_urls``
    Lists of frontend URLs to be appended to the usual frontend URLs.

``front_urls_post``
    Lists of frontend URLs to be appended to the usual frontend URLs, even after ``front_urls``.
    Most of the time, ``front_urls`` should do.

``front_urls_pre``
    Lists of frontend URLs to be prepended to the usual frontend URLs.
    Most of the time, ``front_urls`` should do.

``notify_action``
    Notification framework `~shoop.notify.Action` classes.

``notify_condition``
    Notification framework `~shoop.notify.Condition` classes.

``notify_event``
    Notification framework `~shoop.notify.Event` classes.

``order_source_modifier_module``
    `~shoop.core.order_creator.OrderSourceModifierModule` for modifying
    order source, e.g. in its
    `~shoop.core.order_creator.OrderSource.get_final_lines`.

``pricing_module``
    Pricing module classes; the pricing module in use is set with the ``SHOOP_PRICING_MODULE`` setting.

``service_behavior_component_form``
    Forms for creating service behavior components in Shop Admin.  When
    creating a custom `service behavior component
    <shoop.core.models.ServiceBehaviorComponent>`, provide a form for it
    via this provide.

``service_provider_admin_form``
    Forms for creating service providers in Shop Admin.  When creating a
    custom `service provider <shoop.core.models.ServiceProvider>`
    (e.g. `carrier <shoop.core.models.Carrier>` or `payment processor
    <shoop.core.models.PaymentProcessor>`), provide a form for it via
    this provide.

``supplier_module``
    Supplier module classes (deriving from `~shoop.core.suppliers.base.BaseSupplierModule`),
    as used by `~shoop.core.models.Supplier`.

``tax_module``
    Tax module classes; the tax module in use is set with the ``SHOOP_TAX_MODULE`` setting.

``xtheme``
    XTheme themes (full theme sets).

``xtheme_plugin``
    XTheme plugins (that are placed into placeholders within themes).

``xtheme_resource_injection``
    XTheme resources injection function that takes current context and content as parameters.

Campaigns Provide Categories
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``campaign_catalog_filter``
    Filters that filter product catalog queryset to find the matching campaigns.

``campaign_context_condition``
    Context Conditions that matches against the current context in shop to see if campaign matches.

``campaign_basket_condition``
    Conditions that matches against the order source or source lines in basket.
