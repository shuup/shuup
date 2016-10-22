Shuup Change Log
================

Unrealeased
-----------

- List all changes after last release here (newer on top).  Each change
  on a separate bullet point line.  Wrap the file at 79 columns or so.
  When releasing next version, the "Unreleased" header will be replaced
  with appropriate version header and this help text will be removed.

Core
~~~~

- Populate some unfilled customer fields from order

Localization
~~~~~~~~~~~~

Admin
~~~~~

- Make form modifiers reusable. Users of `ShipmentFormModifier`
  should update any references to implement the
  `shuup.admin.form_modifier.FormModifier` interface instead
- Add mass actions to products list
- Add mass actions to orders list
- Add mass actions to contacts list
- Picotable lists now support mass actions.

Addons
~~~~~~

Front
~~~~~

- Fix search result styling for products with long names
- Restrict the paginator to show at most five pages
- Enable option to use login and register checkout phases
  with vertical checkout process
- Add checkout view with option to login and register
- Add is_visible_for_user method for checkout view phase
- Add recently viewed products app
- Fix/refactor single page checkout view

Xtheme
~~~~~~

Classic Gray Theme
~~~~~~~~~~~~~~~~~~

Simple Supplier
~~~~~~~~~~~~~~~

Order Printouts
~~~~~~~~~~~~~~~

Campaigns
~~~~~~~~~

Customer Group Pricing
~~~~~~~~~~~~~~~~~~~~~~

Discount Pricing
~~~~~~~~~~~~~~~~

Simple CMS
~~~~~~~~~~

Default Tax
~~~~~~~~~~~

Guide
~~~~~

Importer
~~~~~~~~

Regions
~~~~~~~

General/miscellaneous
~~~~~~~~~~~~~~~~~~~~~

SHUUP 0.5.1
-----------

Released on 2016-10-12 09:30pm -0800.

Core
~~~~

- Fetch support id for shops sending telemetry
- Remove shop languages, category, tax class, service provider and services
  default record creation from `shuup_init` management command

Admin
~~~~~

- Add quicklink menu for frequently accessed actions
- Add shop home page that shows steps required to set up a shop for deployment
- Add shop setup wizard for admins to configure the shop, services available,
  and themes
- Add admin comment section to order module

Front
~~~~~

- For search add default sorting based on distance between product
  name and query string
- Add results from words in query to the search until the limit is reached
- Enable filtering product lists by price
- Enable option to filter products with variation values
- Enable option to modify products queryset in category
  and search views
- Add option to limit product list page size
- Add option to sort products by date created
- Change the way product order boxes are being rendered in front.
  Note: This causes backwards incompatibility with templates, so
  fix your templates before upgrading into this version.
- Add option to filter product lists by category
- Configure category and search sorts and filters.
    - Add option to configure category sorts and filters
    - Enable option to configure sorts and filters for search.
    - Activate option for manufacturer filter
    - This change should be noted when updating latest
      front for projects using `shuup.front`
- Fix macro name in Single Page Checkout
- Add Saved Carts to Dashboard
- Add Order History to Dashboard
- Add Customer Information to Dashboard
- Add Dashboard for customers

Classic Gray Theme
~~~~~~~~~~~~~~~~~~

- Fix issue with footer padding

Campaigns
~~~~~~~~~

- Fix bug in product type catalog filter matching
- Avoid matching inactive filters and conditions

Regions
~~~~~~~

- Make backend more modular to allow more specific resource distribution

General/miscellaneous
~~~~~~~~~~~~~~~~~~~~~

- Personal Order history: URL has now been changed from ``/orders`` to ``/order-history``

SHUUP 0.5.0
-----------

Released on 2016-09-29 12:20pm -0800.

Admin
~~~~~

- Enable login with email
- Update menu

Core
~~~~

- Fix bug in prices
   - Avoid calculations based on rounded values
   - Round tax summary values so that the prices shown in
     summary matches with order totals

General/miscellaneous
~~~~~~~~~~~~~~~~~~~~~

- Add support for Django 1.9.x

SHUUP 0.4.7
-----------

Released on 2016-09-20 3:45pm -0800.

Admin
~~~~~

- Give proper error message when saving product with duplicate SKU
- Fix bug in Picotable sorting with translated models
- Fix bug in services list views columns

Front
~~~~~

- Enhance default footer

SHUUP 0.4.6.1
-------------

Released on 2016-09-12 3:45pm -0800.

Core
~~~~

- Do not render region twice in default address formatter

Front
~~~~~

- Fix unicode decode errors in notify events

Importer
~~~~~~~~

- Fix critical bug with log messages

Regions
~~~~~~~

- Fix bug in regions encoding for Python 2

SHUUP 0.4.6
-----------

Released on 2016-09-11 8:00pm -0800.

Core
~~~~

- At default address model form. Force resave if address is assigned
   multiple times
- Provide default address form for mutable addresses

Localization
~~~~~~~~~~~~

Admin
~~~~~

- Use default address form from core in contact address edit
- Add object created signal
- Enable region codes for contact addresses
- Enable region codes for order editor

Addons
~~~~~~

Front
~~~~~

- Use default address form from core for customer information and
   checkout address.
- Move SHUUP_FRONT_ADDRESS_FIELD_PROPERTIES to core and rename it to
   SHUUP_ADDRESS_FIELD_PROPERTIES.
- Fix bug in simple search with non public products
- Add carousel app
   - Note! Instances using shuup-carousel addon should be updated to use
     this new app. There is no migration tools for old carousel and the old
     carousels and slides needs to be copied manually to new app before
     removing shuup-carousel addon from installed apps.
- Enable region codes for checkout addresses

Xtheme
~~~~~~

Classic Gray Theme
~~~~~~~~~~~~~~~~~~

Simple Supplier
~~~~~~~~~~~~~~~

Order Printouts
~~~~~~~~~~~~~~~

- Add option to render printouts as HTML
- Add options to send printouts as email attachments
- Move printouts to tab from toolbar

Campaigns
~~~~~~~~~

Customer Group Pricing
~~~~~~~~~~~~~~~~~~~~~~

Discount Pricing
~~~~~~~~~~~~~~~~

Simple CMS
~~~~~~~~~~

Default Tax
~~~~~~~~~~~

Guide
~~~~~

Importer
~~~~~~~~

- Add Customer Importer
- Add Product Importer
- Add Importer

Regions
~~~~~~~

- Initial version of region app
   - Stores the information about country regions
   - Will populate region code fields in front checkout,
     admin contact and admin order creator addresses

General/miscellaneous
~~~~~~~~~~~~~~~~~~~~~


SHUUP 0.4.5
-----------

Released on 2016-09-04 3:45pm -0800.

Core
~~~~

- Update tax name max length to 124 characters
- Fix issue with package product validation errors in order creator
- Fix bug in product and category slug generation

Admin
~~~~~

- Add lang parameter for JS catalog load
- Add key prefix to JavaScript catalog cache
- Allow shop language to be set via admin
- Allow form group edit views to show errors as messages

Front
~~~~~

- Fix handling of package products in basket
- Notify customer of unorderable basket lines
- Load JS catalog for superusers

Xtheme
~~~~~~

- Skip adding JS-catalog for editing

Default Tax
~~~~~~~~~~~

- Change postal codes pattern to textfield

General/miscellaneous
~~~~~~~~~~~~~~~~~~~~~

- MultiLanguageModelForm: Avoid partially/empty translation objects
   - Delete untranslated objects from database
   - Only set translation object to database if it is translated
   - Ensure required fields if language is partially translated
- MultiLanguageModelForm: Use Parler default as a default

SHUUP 0.4.4
-----------

Released on 2016-08-28 6:40pm -0800.

Core
~~~~

- Most models are now loggable
- Add visibility field to ShopProduct

Localization
~~~~~~~~~~~~

Admin
~~~~~

- Change Picotable columns default behavior
- Match everywhere in Select2 when no model set
- Make currency field a dropdown in Shops admin
- Add possibility to select visible fields in most list views
- Prevent shipping orders without a defined shipping address

Addons
~~~~~~

Front
~~~~~

- Fix category view pagination
- Fix category view rendering for ajax requests
- Fix product search to only show searchable products
- Rename `get_visible_products` to `get_listed_products`
- Define simple search result list column width in less instead of template

Xtheme
~~~~~~

- Add multiple stylesheet option for themes

Classic Gray Theme
~~~~~~~~~~~~~~~~~~

- Add blue and pink color schemes for the theme

Simple Supplier
~~~~~~~~~~~~~~~

- Make stock management columns static

Order Printouts
~~~~~~~~~~~~~~~

Campaigns
~~~~~~~~~

- Campaigns are now loggable

Customer Group Pricing
~~~~~~~~~~~~~~~~~~~~~~

Discount Pricing
~~~~~~~~~~~~~~~~

Simple CMS
~~~~~~~~~~

Default Tax
~~~~~~~~~~~

Guide
~~~~~

General/miscellaneous
~~~~~~~~~~~~~~~~~~~~~

* Fix bug in importing macro in registration app
* Fix bug in pdf utils while fetching static resources

SHUUP 0.4.3
-----------

Released on 2016-08-21 22:40pm -0800.

Core
~~~~

- Prevent Shuup from loading if Parler related settings are missing
- Prevent shipping products with insufficient physical stock
- Telemetry is now being sent if there is no previous submission
- ``CompanyContact.full_name`` now returns name and name extension (if available)

Admin
~~~~~

- Show fewer pagination links for picotable list views
- Product edit: Convert collapsed sections into tabs
- Increment quantity when quick adding products with existing lines in order creator
- Add option for automatically adding product lines when creating order
- Order editing: Tax number is now shown for Company Contacts

Front
~~~~~

- Refactor default templates to allow better extensibility
  - Split up templates to small parts to allow small changes to template without
    overriding the whole template
  - Move included files to macros
  - Split up macros and enable overriding individual macros
  - Update front apps and xtheme plugins based on these changes in macros
  - This change will probably cause issues with existing themes and
    all existing themes should be tested over this change before updating
    to live environment.
- Add product SKU to searchable fields for simple search
- Limit search results for simple search
- Fix password recovery form bug with invalid email
- Show order reconfirmation error if product orderability changes on order
  confirmation
- Exclude unorderable line items from basket

Campaigns
~~~~~~~~~

- Campaigns affecting a product are now shown on product page in admin


SHUUP 0.4.2
-----------

Released on 2016-08-12 03:00pm -0800.

Core
~~~~

- Fix `FormattedDecimalField` default value for form fields
- Combine `TreeManager` and `TranslatableManager` querysets for categories
- Exclude deleted orders from valid queryset
- Enable soft delete for shipments

Admin
~~~~~

- Fix missing shipping_address on orders views
- Add contact type filter to contact list view
- Allow billing address to be used as shipping address on contact creation
- Split person contact and company contact creation into separate actions
- Rearrange product creation and edit pages so that all pertinent info is
  visible simultaneously
- Allow content blocks to be initialized as collapsed
- Add ``admin_product_toolbar_action_item`` provider for product edit toolbar
- Add deprecation warning for ``admin_contact_toolbar_button`` usages
- Add ``admin_contact_toolbar_action_item`` provider for contact toolbar
- Use last product id + 1 as default SKU when creating new products
- Add deprecation warning for ``admin_order_toolbar_button`` usages
- Add ``admin_order_toolbar_action_item`` provider for order toolbar
- Improve category list view parent/child representation and filtering
- Add picotable select2 and MPTT filters
- Hide cancelled orders by default from orders lists
- Add option to delete shipments
- Apply picotable text filters on change rather than on enter/on focus out

Classic Gray Theme
~~~~~~~~~~~~~~~~~~

- Move plugins to Xtheme. Move static_resources, templates and views under
  front and front apps.

Order Printouts
~~~~~~~~~~~~~~~

- Move ``shuup/order_printouts/pdf_export.py`` to ``shuup/utils/pdf.py``

General/miscellaneous
~~~~~~~~~~~~~~~~~~~~~

- Add browser testing capability

Reporting
~~~~~~~~~

- Add Sales Report
- Add Total Sales Report
- Add Sales Per Hour Report
- Add Reporting core

SHUUP 0.4.1
-----------

Released on 2016-08-02 07:30pm -0800.

Core
~~~~

- Add `get_customer_name` for `Order`
- Exclude images from product `get_public_media`
- Add parameter to `PriceDisplayFilter` to specify tax display mode
- Add soft deletion of categories
- Add support to sell products after stock is zero
- Fix refunds for discount lines
- Fix restocking issue when refunding unshipped products
- Make payments for `CustomPaymentProcessor` not paid by default
- Fix shipping status for orders with refunds
- Fix bug in order total price rounding
- Fix bug with duplicates in `Product.objects.list_visible()`
- Fix restocking issues with refunded products
- Add separate order line types for quantity and amount refunds
- Add `can_create_shipment` and `can_create_payment` to `Order`
- Ensure refund amounts are associated with an order line
- Fix tax handling for refunds
- Fix bug: Prevent duplicate categories from all_visible-filter
- Add support for using pricing templatetags for services
- Make refund creation atomic
- Allow refund only for non editable orders
- Create separate refund lines for quantities and amounts
- Fix handling of refunds for discounted lines

Admin
~~~~~

- Fix product variation variable delete for non-english users
- Fix product "Add new image" link
- Fix content block styles that are styled by id
- Add Orders section to product detail page
- Add `admin_product_section` provide to make product detail extendable
- Fix bug with empty customer names in order list view
- Add warning when editing order with no customer contact
- Show account manager info on order detail page
- Remove "Purchased" checkbox from product images section
- Trim search criteria when using select2 inputs
- Fix bug in permission change form error message
- Limit change permissions only for superusers
- Add warning to order creator when creating duplicate contacts
- Show discounted unit price on order confirmation page
- Add order address validation to admin order creator
- Fix bug when editing anonymous orders
- Show order line discount percentage in order detail and creator views
- Allow superadmins to login as customer
- Show orderability errors in package product management
- Show stocks in package product management
- Add link to order line product detail page in order editor
- Add product line quick add to order creator
- Add product barcode field to searchable select2 fields
- Filter out deleted products from Stock Management list view
- Show newest contacts and users first in admin list views
- Show list of shipments in order view
- Fix customer, creator, and ordered by links on order detail page
- Prevent picotable from reloading after every change
- Add ability to copy category visibility settings to products
- Reorganize main menu
- Show customer comment on order detail page
- Redirect to order detail page on order submission
- Make contact views extendable
- Make generic Section object for detail view sections
- Display shipment form errors as messages
- Populate tax number from contact for admin order creator
- Move various dashboard blocks to own admin modules
- Prevent shipments from being created for refunded products
- Add `StockAdjustmentType` Enum
- Fix payment and shipment visibility in Orders admin
- Manage category products from category edit view
- Filter products based on category
- Add permission check for dashboard blocks
- Fix required permission issues for various modules
- Make `model_url` context function and add permission check
- Add permission check option to `get_model_url`
- Add permission check to toolbar button classes
- Enable remarkable editor for service description
- Add option to filter product list with manufacturer
- Remove orderability checks from order editor
- Replace buttons with dropdown in Orders admin

Front
~~~~~

- Checkout show company form validation errors for fields
- Do not show messages in registration if activation is not required
- Show public images only on the product detail page
- Add ability for customers to save their cart
- Ensure email is not blank prior to sending password recovery email
- Send notify event from company created
- Send notify event from user registration
- Fix bug in cart list view with empty taxful total price
- Fix single page checkout for customers not associated with a company
- Use contact default addresses for company creation
- Use home country by default in customer information addresses


Classic Gray Theme
~~~~~~~~~~~~~~~~~~

- Enable copy between customer information addresses
- Honor customer group pricing options for services
- Enable markdown for service description

Simple Supplier
~~~~~~~~~~~~~~~

- Add stock limit notification event
- Skip refund lines when getting product stock counts


Campaigns
~~~~~~~~~

- Fix bug with campaign discount amounts
- Add category products basket condition and line effect
- Enable exact quantity matches for products in basket campaigns

Customer Group Pricing
~~~~~~~~~~~~~~~~~~~~~~

- Re-style contactgroup pricing admin form


Simple CMS
~~~~~~~~~~

- Show error when attempting to make a page a child of itself
- Fix plugin links

Guide
~~~~~

- Fix admin search for invalid API URL settings


Shuup 0.4.0
-----------

Released on 2016-06-30 06:00 +0300.

The first Shuup release.

Content of Shuup 0.4.0 is same as :doc:`Shoop 4.0.0 <shoop-changelog>`
with all "shoop" texts replaced with "shuup".
