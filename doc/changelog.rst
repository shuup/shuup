Shuup Change Log
================

Released on 2016-08-12 03:00pm -0800.

Core
~~~~

- Fix `FormattedDecimalField` default value for form fields
- Combine `TreeManager` and `TranslatableManager` querysets for categories
- Exclude deleted orders from valid queryset
- Enable soft delete for shipments

Admin
~~~~~

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
