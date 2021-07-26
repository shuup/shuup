The Provides system
===================

The Provides system is Shuup's mechanism for discovering and loading
components, both first-party and third-party.  Shuup apps use
the provides system in various ways.

* The core itself uses Provides for discovering method and supplier modules.
* ``shuup.admin`` uses Provides to load admin modules, form customizations etc.
* ``shuup.front`` uses it for URLconf overrides etc.

The provide categories used by Shuup are listed in :ref:`provide-categories`, but you
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


Blacklisting Provides
---------------------

Shuup also supports blacklisting unwanted provides. This is useful when one want to disable
some features like shipping and payment methods provided by a single app. This way,
it is easy to select which provides should be loaded by Shuup.
To blacklist provides, you need to set a special Django setting named `SHUUP_PROVIDES_BLACKLIST`:

.. code-block:: python

   SHUUP_PROVIDES_BLACKLIST = {
        'service_provider_admin_form': [
            'pigeon.admin_forms:PigeonShippingAdminForm'
        ]
    }

This will allow the spec `pigeon.admin_forms:PigeonShippingAdminForm` from category
`service_provider_admin_form` to be loaded.


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
    Additional ``FormPart`` classes for Category editing. See :doc:`example <../howto/new_tab>`.

``admin_contact_form_part``
    Additional ``FormPart`` classes for Contact editing. See :doc:`example <../howto/new_tab>`.

``admin_contact_group_form_part``
    Additional ``FormPart`` classes for ContactGroup editing. See :doc:`example <../howto/new_tab>`.

``admin_contact_toolbar_action_item``
    Additional ``DropdownItem`` subclass for Contact detail action buttons.

``admin_contact_edit_toolbar_button``
    Additional ``BaseActionButton`` subclasses for Contact edit.
    Subclass init should take current contact as a parameter.

``admin_contact_section``
    Additional ``Section`` subclasses for Contact detail sections.

``admin_extend_create_shipment_form``
    Allows providing extension for shipment creation in admin.
    Should implement the `~shuup.admin.form_modifier.FormModifier` interface.

``admin_main_menu_updater``
    Allows updating the Admin Main Menu with new elements. The objects offered through this
    provide should inherit from ``~shuup.core.utils.menu.MainMenuUpdater`` class.

``admin_mass_actions_provider```
    Object that provides mass actions to all views.
    Providers must subclass from ``shuup.admin.utils.picotable.PicotableMassActionProvider``
    and implement the ``get_mass_actions_for_view`` method.

``admin_module``
    Admin module classes. Practically all of the functionality in the admin is built
    via admin modules.

``admin_object_selector``
    Object selector classes for filtering models in select2 objects.
    Providers must subclass from `~shuup.admin.views.select.BaseAdminObjectSelector` class.

``admin_order_information``
    Additional information rows for Order detail page. Provide objects should inherit
    from `~shuup.admin.modules.orders.utils.OrderInformation` class.

``admin_product_form_part``
    Additional ``FormPart`` classes for Product editing.
    (This is used by pricing modules, for instance.) See :doc:`example <../howto/new_tab>`.

``admin_product_section``
    Additional ``Section`` subclasses for Product edit sections.

``admin_product_validator``
    Provide an AdminProductValidator class, which validates a product according to some criteria.

``admin_product_toolbar_action_item``
    Additional ``DropdownItem`` subclass for Product edit action buttons.

``admin_template_injector``
    Allow snippet injection inside admin templates. The classes must inherit
    from the ``~shuup.admin.base.AdminTemplateInjector`` class.

``admin_shop_edit_toolbar_button``
    Additional ``BaseActionButton`` subclasses for Shop edit.
    Subclass init should take current shop as a parameter. Current shop is
    passed to static method ``visible_for_object`` to check whether to actually
    show the item.

``admin_shop_form_part``
    Additional ``FormPart`` classes for Shop editing. See :doc:`example <../howto/new_tab>`.

``admin_toolbar_button_provider``
    Object that provides buttons to all toolbars.
    Providers must subclass from ``shuup.admin.toolbar.BaseToolbarButtonProvider``
    and implement the ``get_buttons_for_view`` method.

``basket_command_middleware``
    Injects a middleware in the basket command dispatcher that can be used
    to mutate the basket kwargs and response and execute additional steps
    with the basket once a command is invoked.

``customer_dashboard_items``
    Classes to parse customer dashboard items from. These are subclasses of
    ``shuup.front.utils.dashboard.DashboardItem``

``discount_module``
    `~shuup.core.pricing.DiscountModule` for pricing system.

``front_extend_product_list_form``
    Allows providing extension for product list form. Should implement the
    `~shuup.front.utils.sorts_and_filters.ProductListFormModifier`
    interface.

``front_service_checkout_phase_provider``
    Allows providing a custom checkout phase for a service (e.g. payment
    method or shipping method). Should implement the
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

``front_model_url_resolver``
    List of functions that resolve a model instance into an object URL.
    The first valid url returned by a provide will be used by the caller.

``admin_model_url_resolver``
    List of functions that resolve a model instance into an object URL.
    The first valid url returned by a provide will be used by the called.

``admin_browser_config_provider```
    List of classes that implements ``shuup.admin.browser_config.BaseBrowserConfigProvider`` class.
    It can implement the ``get_browser_urls`` method which should returns a dictionary of urls names
    that should be exported to the browser through the ``window.ShuupAdminConfig.browserUrls`` object.
    The returned dictionary should have the url name as the value, which will be reversed when
    rendering the templates.
    It can also implement the ``get_gettings`` method which should returns a dictionary.
    The returned data will be converted into JSON and exported to the browser
    through the ``window.ShuupAdminConfig.settings`` object.

``front_menu_extender``
    Additional menu items provided by addons. These should be subclassed from
    `~shuup.xtheme.extenders.FrontMenuExtender`.

``front_product_order_form``
    List of order forms which are subclasses of ``ProductOrderForm``. These forms
    are shown on product detail page in front as well as previews etc.

``front_registration_field_provider``
    List of ``FormFieldProvider`` classes. These classes provide ``FormFieldDefinition``
    objects which extend registration forms accross the Shuup front.

``checkout_confirm_form_field_provider``
    List of ``FormFieldProvider`` classes. These classes provide ``FormFieldDefinition``
    objects which extend checkout confirm form.

``front_auth_form_field_provider``
    List of ``FormFieldProvider`` classes. These classes provide ``FormFieldDefinition``
    objects which extend authentication forms accross the Shuup front.

``front_company_registration_form_provider``
    List of ``FormDefProvider`` classes. These classes provide ``FormDefinition``
    objects which extend the ``CompanyRegistrationForm`` with ``form_defs``.

``front_urls``
    Lists of frontend URLs to be appended to the usual frontend URLs.

``front_urls_post``
    Lists of frontend URLs to be appended to the usual frontend URLs, even after ``front_urls``.
    Most of the time, ``front_urls`` should do.

``front_urls_pre``
    Lists of frontend URLs to be prepended to the usual frontend URLs.
    Most of the time, ``front_urls`` should do.

``front_line_properties_descriptor``
    Object that returns properties for order source lines and order lines
    to be rendered in the basket and order detail views.
    The objects must inherit from the `~shuup.front.utils.order_source.BaseLinePropertiesDescriptor` base class.

``notify_action``
    Notification framework `~shuup.notify.Action` classes.

``notify_condition``
    Notification framework `~shuup.notify.Condition` classes.

``notify_event``
    Notification framework `~shuup.notify.Event` classes.

``notify_script_template``
    Notification framework `~shuup.notify.base.ScriptTemplate` classes.

``order_printouts_delivery_extra_fields``
    Additional information rows for order delivery printout. Provide objects should inherit
    from `~shuup.order_printouts.utils.PrintoutDeliveryExtraInformation` class.

``order_source_modifier_module``
    `~shuup.core.order_creator.OrderSourceModifierModule` for modifying
    order source, e.g. in its
    `~shuup.core.order_creator.OrderSource.get_final_lines`.

``order_source_validator``
    List of classes that validate a given `~shuup.core.order_creator.OrderSource` and return an error iterator.
    The class must have a ``get_validation_errors`` class method which receives the ``order_source`` and returns/yields
    ``ValidationError`` instances.

``pricing_module``
    Pricing module classes; the pricing module in use is set with the ``SHUUP_PRICING_MODULE`` setting.

``product_kind_specs``
    List of classes that define the product kinds that can be used in the platform.
    The classes must implement the `~shuup.core.specs.product_kind.ProductKindSpec` base class.
    It is specially used to control which supplier modules can handle certain types of products
    and also to hide products from the normal admin product list.

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

``carrier_wizard_form_def``
    `Formdefs <shuup.utils.form_group.FormDef>` for creating carriers
    (and their service(s)) through the shop setup wizard.

``payment_processor_wizard_form_def``
    `Formdefs <shuup.utils.form_group.FormDef>` for creating payment processors
    (and their service(s)) through the shop setup wizard.

``product_context_extra``
    Additional context data for the front product views. Provide objects should inherit
    from `~shuup.front.utils.ProductContextExtra` class.

``product_subscription_option_provider``
    Returns subscription options for a given `~shuup.core.utils.product_subscription.ProductSubscriptionContext` context.
    The provider must inherit from the base class `~shuup.core.utils.product_subscription.BaseProductSubscriptionOptionProvider`.

``supplier_module``
    Supplier module classes (deriving from `~shuup.core.suppliers.base.BaseSupplierModule`),
    as used by `~shuup.core.models.Supplier`.

``tax_module``
    Tax module classes; the tax module in use is set with the ``SHUUP_TAX_MODULE`` setting.

``xtheme``
    XTheme themes (full theme sets).

``xtheme_layout``
    XTheme layouts (to split placeholders different types of layouts with different visibilities).

``xtheme_plugin``
    XTheme plugins (that are placed into layouts within themes).

``xtheme_resource_injection``
    XTheme resources injection function that takes current context and content as parameters.

``xtheme_snippet_blocker``
    Blocker classes that can prevent a global snippet from being injected


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

``report_writer_populator``
    List of functions to populate report writers. This allows the creation of custom output formats.
    Should follow the signature of `~shuup.reports.writer.populate_default_writers`.

Simple CMS Provide Categories
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``admin_page_form_part``
    Additional ``FormPart`` classes for Page editing. See :doc:`example <../howto/new_tab>`.

``simple_cms_template``
    List of available template objects that can be used to render CMS pages.

List of objects that have provides key as attributes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Some objects have attributes that contain a provide key which are used to load provides dynamically.
They are specially used in mixins when they can be attached to some class which overrides the attribute
with its own provide key name, making it easier to extend provides related to class. Here is the list
of objects that have this attribute which can be overrided on a specialization:

``FormPartsViewMixin.form_part_class_provide_key``
    Adds form parts to a view dynamically. Each view will have a custom provide key value.

``View.toolbar_buttons_provider_key``
    Adds buttons to a view's toolbar. Each view will have a custom provide key value.
    Only views that use toolbars can use this attribute, as in ``PicotableViewMixin``.
    Check `~shuup.admin.modules.categories.views.list.CategoryListView` for an example.

``View.mass_actions_provider_key``
    Adds mass actions view. Each view will have a custom provide key value.
    Only views that inherints from ``PicotableListView`` or ``PicotableViewMixin`` will have mass actions added.
    All providers must inherit from `PicotableMassActionProvider` base class.
    Check `~shuup.admin.modules.categories.views.list.CategoryListView` for an example.
