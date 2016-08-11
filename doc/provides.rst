The Provides system
===================

The Provides system is Shuup's mechanism for discovering and loading
components, both first-party and third-party.  Shuup apps use
the provides system in various ways.

* The core itself uses Provides for discovering method and supplier modules.
* ``shuup.admin`` uses Provides to load admin modules, form customizations etc.
* ``shuup.front`` uses it for URLconf overrides etc.

The provide categories used by Shuup are listed in :ref:`provide-categories` but you
can also define your own categories as you wish.

.. TODO:: Document the various ways better.

Provides are grouped under different categories, such as ``admin_module``,
``xtheme_plugin``, ``front_urls``, etc.

Declaring Provides
------------------

Shuup uses the Django 1.7+ ``AppConfig`` system to declare provides.

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

Provide management functions are found in the :mod:`shuup.apps.provides` module.

In general, the :obj:`shuup.apps.provides.get_provide_objects` method is your most useful
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

``admin_contact_group_form_part``
    Additional ``FormPart`` classes for ContactGroup editing

``admin_contact_toolbar_action_item``
    Additional ``DropdownItem`` subclass for Contact detail action buttons.

``admin_contact_edit_toolbar_button``
    Additional ``BaseActionButton`` subclasses for Contact edit.
    Subclass init should take current contact as a parameter.

``admin_contact_section``
    Additional ``Section`` subclasses for Contact detail sections.

``admin_extend_create_shipment_form``
    Allows providing extension for shipment creation in admin.
    Should implement the
    `~shuup.admin.modules.orders.views.shipment.ShipmentFormModifier`
    interface.

``admin_product_form_part``
    Additional ``FormPart`` classes for Product editing.
    (This is used by pricing modules, for instance.)

``admin_product_section``
    Additional ``Section`` subclasses for Product edit sections.

``admin_product_toolbar_action_item``
    Additional ``DropdownItem`` subclass for Product edit action buttons.

``admin_shop_form_part``
    Additional ``FormPart`` classes for Shop editing.

``admin_module``
    Admin module classes. Practically all of the functionality in the admin is built
    via admin modules.

``discount_module``
    `~shuup.core.pricing.DiscountModule` for pricing system.

``front_service_checkout_phase_provider``
    Allows providing a custom checkout phase for a service (e.g. payment
    method or shipping method).  Should implement the
    `~shuup.front.checkout.ServiceCheckoutPhaseProvider` interface.

``front_template_helper_namespace``
    Additional namespaces to install in the ``shuup`` "package" within
    template contexts.
    .. seealso:: :ref:`custom-template-helper-functions`

``admin_order_toolbar_action_item``
    Additional ``DropdownItem`` subclass for Order detail action buttons.
    Current order is passed to subclass init and static method ``visible_for_object``
    is called for the subclass to check whether to actually show the item.

``admin_order_section``
    Additional ``Section`` subclasses for Order detail sections.

``front_urls``
    Lists of frontend URLs to be appended to the usual frontend URLs.

``front_urls_post``
    Lists of frontend URLs to be appended to the usual frontend URLs, even after ``front_urls``.
    Most of the time, ``front_urls`` should do.

``front_urls_pre``
    Lists of frontend URLs to be prepended to the usual frontend URLs.
    Most of the time, ``front_urls`` should do.

``notify_action``
    Notification framework `~shuup.notify.Action` classes.

``notify_condition``
    Notification framework `~shuup.notify.Condition` classes.

``notify_event``
    Notification framework `~shuup.notify.Event` classes.

``order_source_modifier_module``
    `~shuup.core.order_creator.OrderSourceModifierModule` for modifying
    order source, e.g. in its
    `~shuup.core.order_creator.OrderSource.get_final_lines`.

``pricing_module``
    Pricing module classes; the pricing module in use is set with the ``SHUUP_PRICING_MODULE`` setting.

``service_behavior_component_form``
    Forms for creating service behavior components in Shop Admin.  When
    creating a custom `service behavior component
    <shuup.core.models.ServiceBehaviorComponent>`, provide a form for it
    via this provide.

``service_provider_admin_form``
    Forms for creating service providers in Shop Admin.  When creating a
    custom `service provider <shuup.core.models.ServiceProvider>`
    (e.g. `carrier <shuup.core.models.Carrier>` or `payment processor
    <shuup.core.models.PaymentProcessor>`), provide a form for it via
    this provide.

``supplier_module``
    Supplier module classes (deriving from `~shuup.core.suppliers.base.BaseSupplierModule`),
    as used by `~shuup.core.models.Supplier`.

``tax_module``
    Tax module classes; the tax module in use is set with the ``SHUUP_TAX_MODULE`` setting.

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

``campaign_product_discount_effect_form``
   Form for handling product discount effects of a catalog campaign.
   Should be a ModelForm with its model being a subclass of
   `~shuup.campaigns.models.ProductDiscountEffect`.

``campaign_basket_condition``
    Conditions that matches against the order source or source lines in basket.

``campaign_basket_discount_effect_form``
    Form for handling discount effects of a basket campaign. Should be
    a ModelForm with its model being a subclass of
    `~shuup.campaigns.models.BasketDiscountEffect`.

``campaign_basket_line_effect_form``
    Form for handling line effects of a basket campaign. Should be a
    ModelForm with its model being a subclass of
    `~shuup.campaigns.models.BasketLineEffect`.

Reports Provide Categories
~~~~~~~~~~~~~~~~~~~~~~~~~~

``reports``
    Class to handle report data collection. Should be a subclass of `~shuup.reports.report.ShuupReportBase`.
