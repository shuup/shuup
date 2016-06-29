Shoop Change Log
================

Shoop 4.0.0
-----------

Released on 2016-06-29 21:30 +0300.

Core
~~~~

- Fix bug: Category model is missing MPTT ordering options
- Add staff only behavior component
- Add refund-related methods to ``Order``
- Add ``OrderLineType.REFUND`` enum type
- Update order phone max length to 64 characters
- Add cash payment method
- Add rounding behavior component
- Add contact group availability behavior component
- Fix bug: Do not display decimal values in scientific notation
- Fix bug: Taxes of child order lines are filled incorrectly
- Fix bug: Order line parent lines are not linked
- Add modified on for ``Order``
- Add modified by for ``Order`` and ``OrderSource``
- Add ``get_company_contact`` to ``shoop.core.models``
- Implement taxing of lines without tax class
- Add new abstract method ``get_taxed_price`` to ``TaxModule``
- Add ``ShopProduct.is_visible``
- Add ``Order.can_edit``
- Update shipping status correctly in ``Order.create_shipment``
- Add ``OrderModifier`` for modifying orders with ``OrderSource``
- Add option use ``Order.create_shipment`` with unsaved ``Shipment``
- Add identifier for ``Shipment``
- Fix bug: Fix max length for service method names for ``Order``
- Make ``Order.create_payment`` also do status update for partially paid
- Add ``get_total_unpaid_amount`` method to ``Order``
- Add ``is_canceled`` and ``can_set_canceled`` to ``Order``
- Fix bug: Convert ``Shipment`` weight to kilograms
- Make ``create_shipment`` for order atomic
- Add ``shipment_created`` signal
- Add ``get_tracking_codes`` to ``shoop.core.models.Order``
- Add weight based pricing behavior component
- Add ``total_gross_weight`` property for ``Source``
- Fix bug: Order line text is not set for package products
- Add new Service API and implement shipping and payments with it
- Remove BaseMethodModule based API (``shoop.core.methods``)
- Add support for custom user model (``AUTH_USER_MODEL``)
- Add management command to generate bought with relations
- Add ``merchant_notes`` text-field to ``Contact``
- Add ``first_name`` and ``last_name`` fields to ``PersonContact``
- Add bought with relation to ``ProductCrossSellType``
- Set customer marketing permission while creating order
- Disable delete for default contact groups
- Allow storing price display options to contact groups
- Add template tags for rendering prices with context specific price
  display options (pretax or with taxes, or hide prices totally)
- Fix bug: ``OrderSource.tax_amount`` always returned zero price
- Add contacts automatically to type specific default groups
- ``OrderCreator`` no longer requires a request
- Add ``order_creator_finished`` signal under ``order_creator``
- Move calculate_taxes_automatically from ``OrderSource`` to ``TaxModule``
- Add shop product validation for OrderSource
- Add option to create payments with REST API
- Add contact address for ``Shop``
- Add update_stock calls for ``SimpleSupplierModule``
- Rename ``CAMPAIGN`` in ``OrderLineType`` enum to ``DISCOUNT``
- Add ``OrderSourceModifierModule`` interface for modifying order source
- Add ``DiscountModule`` interface for pricing
- Simplify ``PricingContext`` and require shop and customer for it
- Add ``get_price_info`` etc. functions to ``shoop.core.pricing``
- Add ``get_suppliable_products`` to ``shoop.core.models.Supplier``
- Add "codes" API to OrderSource and BaseBasket

Localization
~~~~~~~~~~~~

- Add Brazilian Portuguese translations (pt_BR)

Admin
~~~~~

- Add refund creator to order admin
- Add customer detail view to order creator
- Define module-level permissions for all admin modules
- Enable adding of permission groups from users admin
- Add admin module for managing Django permission groups
- Add ``get_required_permission`` to ``AdminModule``
- Add support for module-level permissions
- Use Select2MultipleField for handling contact members
- Add Select2MultipleField
- Add account manager for contact
- Add PersonContact choice widget
- Add barcode filter to product list view
- Show stock in order creator
- Fix bug: Fix decimal precision issues on order creation
- Enable order creation for contact from contact detail view
- Fix bug: Refresh order lines when customer is changed during order creation
- Add default ``is_active`` filter to Contact and User admins
- Enable default values for ``ChoiceFilter``
- Enable contact activation/deactivation
- Allow contact adding and removing for company
- Show companies in person contact edit page
- Add target option to ``SearchResult``
- Filter contacts with group in contact list view
- Hide group members from contact group edit view
- Remove support for select pickers
- Enable multiselect dropdown with Select2
- Enable adding log entries to orders
- Enable order editing
- Allow shipment creation form extensions
- Add payment creation view to ``Order`` admin
- Enable order cancelation in Order edit view
- Hide invalid choices for package products
- Fix bug: Fix convert to parent menu items in ``EditProductToolbar``
- Show tracking codes in order detail
- Fix bug: Show package siblings for variation children
- Fix bug: Detail page of contact with multiple groups fails on Python 3
- Enable add/edit for weight based behavior component through service admin
- Add ``admin_contact_group_form_part`` provider for ``ContactGroup`` admin
- Redo shipping and payment method management
- Add service provider management
- Add package mode for products
- Enable merchant notes editing for contacts
- Add option to add extra form parts to Shop edit view
- Enable delete for contact groups
- Make all enabled shipping and payment methods available in order creator
- Check product quantities in order creation
- Add option to add action buttons to Order edit view

Addons
~~~~~~

- Enable upgrade, migrations and collectstatic from admin

  - Has a known problem in reloading application server.

Front
~~~~~

- Initialize checkout addresses from customer data
- Logout users linked to inactive contact
- Allow user to change password from account settings
- Add login check for inactive contacts
- Remove "Ordering for company" from checkout if logged in
- Allow user to link company contact from account page
- Log-in as company if user is a member of a company
- Make ``get_product_cross_sells`` faster
- Make ``get_best_selling_products`` faster
- Make ``get_visible_products`` faster
- Fix bug with multiple service checkout phases
- Update UI for package products
- Add SHOOP_FRONT_ADDRESS_FIELD_PROPERTIES setting
- Support also django-registration-redux 1.4
- Enable description and logo for methods in checkout
- Add admin view for monitoring customer carts
- Remove ``get_method_validation_errors`` signal
- Fix bug at ``get_visible_products`` filter when orderable_only is False
- Set template price display options from the customer
- Fix bug: BasketStorage.finalize() never called delete() correctly
- Check product quantity already in basket while adding
- Move ``order_creator_finished`` signal under core
- Add "next" parameter support for registration
- Process given coupon codes in basket
- Add ``get_visible_products`` template helper

Xtheme
~~~~~~

- Add custom XThemeModelChoiceField to show admin URLs
- Enhance default text plugin editor to remarkable markdown editor
- Add support for global/multi-view placeholders
- Add generic snippets plugin for doing simple integrations
- Add a plugin for displaying category links on shop front
- Add a linkable image plugin

Classic Gray Theme
~~~~~~~~~~~~~~~~~~

- Add Shoop Wishlist addon support for logged in users
- Hide product order section when prices are hidden
- Hide cart when prices are hidden
- Show tracking codes in order detail
- Remove ``ProductCrossSellType.COMPUTED`` from cross-sells plugin
- Update cross-sells plugin to use ``ProductCrossSellType.BOUGHT_WITH``
- Render prices with the new price rendering template tags
- Show error messages while adding products to basket
- Add "next" parameter to register links
- Add Coupon use possibility to basket page
- Add option to only show orderable products to highlights plugin
- Add Xtheme plugin to display social media links on shop front

Simple Supplier
~~~~~~~~~~~~~~~

- Add admin modules for updating stock
- Add support for stock counts and values

Order Printouts
~~~~~~~~~~~~~~~

- Add app for creating PDF printouts of orders

  - Currently supports printing of Order confirmation and Delivery slips

Campaigns
~~~~~~~~~

- Add campaigns app with following features:

  - Campaigns management
  - Coupon management
  - Contact group sales ranges

Customer Group Pricing
~~~~~~~~~~~~~~~~~~~~~~

- Rename Simple Pricing to Customer Group Pricing
- Fix pricing for ``AnonymousContact``

Discount Pricing
~~~~~~~~~~~~~~~~

- Removed

Simple CMS
~~~~~~~~~~

- Add option to list children on page
- Add possibility to set parent on page

Default Tax
~~~~~~~~~~~

- Filter tax rules by postal codes to gain better performance
- Add minimum and maximum postal code values to ``TaxRule``

Guide
~~~~~

- Add guide app that integrates help documentation into admin search

General/miscellaneous
~~~~~~~~~~~~~~~~~~~~~

- Rename UnitedDecimal to UnittedDecimal
- Add a way to find out min and max values from pattern
- Reword doc/provides.rst


Shoop 3.0.0
-----------

Released on 2016-01-21 11:15 +0200.

Core
~~~~

- Document Shoop tax system
- API and documentation clean-up
- Remove ``AddressManager``
- Split address into mutable and immutable address
- Add Product.get_public_media helper function
- Ensure ``TranslatabelShoopModel.__str__`` doesn't return lazy objects
- Deny price unit changes of in-use ``Shop``
- Assign created customers to ``CustomerTaxGroups`` on creation
- Fix couple tax related terms
- Remove ``PriceTaxContext``
- Add ``PricingContextable`` interface and fix related docstrings
- Remove ``Priceful.total_price``
- Add dynamic configuration API: ``shoop.configuration``
- Fix tax calculations and implement override groups
- Add autoexpiring versioned cache API: ``shoop.core.cache``
- Enable email login and password recovery with username

Localization
~~~~~~~~~~~~

- Add translations for Finnish, Chinese and Japanese
- Add translation extraction tools (``shoop_makemessages``)
- Mark more messages for translation in templates
- Enable JavaScript translations

Admin
~~~~~

- Bump bootstrap-datetimepicker version to 2.3.8
- Show Shoop version number in Admin
- Fix order list sorting and filtering by total price
- Fix CMS page list sorting by title
- JavaScript compilation fixes: Turn our ES6 to ES5 with Babel
- Fix URL encoding in ``redirect_to_login``
- Add view for creating orders from the Admin
- Enable markdown editor for product and category description
- Fix SKU and name initialization when creating a product by search
- Add new template macros
- Refactor templates to use template macros
- Admin form styling and UX updates

Front
~~~~~

- Set default country in checkout address forms
- Fix SHOOP_FRONT_INSTALL_ERROR_HANDLERS setting being not respected
- Change password recover error message

Xtheme
~~~~~~

- Make Xtheme plugins translatable
- Allow addons to inject resources
- Editor improvements
- Fix a crash when trying to revert unsaved configuration

Classic Gray Theme
~~~~~~~~~~~~~~~~~~

- Basket: Hide line base price when it's not positive
- Show product media at order history and product detail pages
- Add language changer to navigation
- Add possibility for other future brand colors
- Add carousel styles for Bootstrap carousel
- Unvendor fonts
- Show maintenance mode for super user
- Fix logo text line height
- Add new placeholders
- Footer CMS Pages field are no longer required
- Update label for footer links to avoid confusion

Default Theme
~~~~~~~~~~~~~

- Remove Default theme from Shoop Base. Moved to
  https://github.com/shuup/shuup-simple-theme

Campaigns
~~~~~~~~~

- Fix admin list view sorting

General/miscellaneous
~~~~~~~~~~~~~~~~~~~~~

- Add Transifex configuration for the ``tx`` command
- Add verbose names to all model and form fields
- Do unit testing from doctests too
- Update Python package dependencies
- Lock down JavaScript dependencies
- Code style improvements
- Add configuration for Travis CI
- Include JS and CSS source maps to the Python package
- Cleanup tax TODOs
- Move apply_request_middleware to testing
- Documentation: Tune Sphinx settings and ignore migrations in API docs
- Fix Eslint complaints
- Make sure that bower is ran non-interactively


Shoop 2.0.0
-----------

Released on 2015-10-05 16:45 +0300.

Admin
~~~~~

- Add basic Manufacturer views
- Basic Supplier management
- Add image field for category
- Fix issue with price not being saved
- Optionally disable creating shops
- Add "Product Media" tab to product editing
- Tabify translated fields
- Variation UI styles
- Media Browser Rehaul
- Add ``ImageChoiceWidget``
- Actually send ``data-filter`` to media browser from browse widgets
- Admin form error indicators
- Add keyboard shortcuts to megasearch
- Show first language tab with errors
- Update styles for admin form error indicators
- Show errors more clearly
- Make folder clicks work at media browser
- Fix paths of generated source maps
- Add styles for bootstrap input-group
- Time interval attribute now renders as ``DecimalField``
- Notify: Add better error handling for "step edit"-popup
- Better variation error handling
- Fix issue where visibility errors caused an error
- Update admin category view
- Admin datetimepicker

Core
~~~~

- Rework ``SimplePricing`` and pricing in general
- Add non-ASCII support for supplier name
- Fix checking of duplicate settings
- Add new fields to shop core
- Add ``DiscountPricingModule``
- Fix PriceInfo usage with non-one quantities
- Fix shoop.core.migrations.0006
- Tax clean-up and refactoring
- Prevent ``Shop`` being deleted when image was deleted

Front
~~~~~

- An all-new dynamic theming system, Xtheme
- Classic Gray: A new slick theme built on the Xtheme system
- Add ordering for cross sells template helper
- Fix ``get_root_categories`` performance
- Maintenance mode
- template_helpers: Fix get_pagination_variables
- Ensure user is logged in after activating account
- Customer URL now requires login
- Add support for Complex variations
- Add Default ErrorHandling
- Fix issue with variation children being listed for admin user
- Front: Fix issue with variation children visible in search results

General/miscellaneous
~~~~~~~~~~~~~~~~~~~~~

- Run ESLint on all the things!
- Prunes, manifests
- PEP8ify
- Various fixes
- Tests: Make test_user_detail_contact_seed not fail randomly
- Miscellaneous tiny fixes
- Fixes
- Cms duplicate
- Embetter patterns
- Saner sanity tools
- Workbench: Allow overriding couple settings from env


Shoop 1.2.0
-----------

Released on 2015-08-24 17:30 +0300.

- Admin: Polyfill forms to ensure IE support

- Fix uniqueness of some InternalIdentifierFields

  - Namely identifier field of Attribute, OrderStatus,
    ProductVariationVariable and ProductVariationVariableValue

- Admin: Show payment details in order views

- Coding Style: Clean-up and sort all imports

- Fix usages of too-direct imports of models

- Fix some unicode/bytes issues by adding "unicode_literals" imports

- Admin layout fixes

  - Update telemetry admin layout and add translations tags

  - Change the attributes icon from product edit to the right one

  - Move attributes in product type edit to it's own tab

  - Hide browser native horizontal scrollbar from main menu

- Admin: Product image management

- Admin: Product Variation management

- Front: Add cross-sells to product detail page in default template

- Admin: Fix menu scrolling

- Upgrade Python and npm dependencies

- Admin: Shop management

- Front: Add link to admin panel in default template

- Admin: Fix product attributes getting cleared unless they were edited

- Admin: Product Sales Unit management

- Admin: Add ProductChoiceWidget for selecting Products

- Admin: Product cross-sell management

- Admin: Styling: Add borders to bootstrap select

- Admin: Fix showing details of a CompanyContact

- Admin: Fix showing current addresses in contact details


Shoop 1.1.0
-----------

Released on 2015-07-03 12:30 +0300.

- Improve "Getting Started with Shoop Development" documentation

- Add a basic REST API for reading/writing products and reading orders

- Use the database to store shopping baskets by default

- Implement pluggable shopping basket storage backends

- Implement basic contact group admin

- Add telemetry (usage statistics) system

- Add Dockerfile

- Improve admin login flow

- Document settings; make documentation builds available on ReadTheDocs

- Make release packaging much more robust

- Generate order keys in a secure manner

- Trim admin search strings

- Embetter admin order layouts

- Create the Shop as active with ``shoop_init`` management command

- Fix usages of ``Category.get_ancestors()`` in templates

- Remove Stripe integration (shoop.stripe)

  - It now lives in https://github.com/shuup/shuup-stripe

- Core: Declare correct ``required_installed_apps`` in AppConfig

- Fix handling of tuple-format ``required_installed_apps``

- Fix Money class to not read settings at instance creation

- Fix management command ``shoop_show_settings`` for Python 3

- Add Addon documentation (doc/addons.rst)


Shoop 1.0.0
-----------

Released on 2015-06-04 16:30 +0300.

- The first Open Source version of Shoop.
