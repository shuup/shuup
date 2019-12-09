Shuup Change Log
================

Unrealeased
-----------

- List all changes after last release here (newer on top).  Each change
  on a separate bullet point line.  Wrap the file at 79 columns or so.
  When releasing next version, the "Unreleased" header will be replaced
  with appropriate version header and this help text will be removed.


Shuup 1.10.1
------------

Released on 2019-12-09 8:15pm +0200.

Admin
~~~~~

- Fix bug with coupon codes

Campaigns
~~~~~~~~~

- Add a variation parent basket condition. This condition will match on each
  child in basket of a chosen product.

Core
~~~~

- Change contactgroup name length to 256 so it is better in line with other
  name fields

Xtheme
~~~~~~

- Fix bug with Select2 in plugin

General
~~~~~~~

- Add ability to display text on top of carousel


Shuup 1.10.0
------------

Released on 2019-11-14 7:15am +0200.

Remove API code and move to separated repositories Shuup API and
Shuup REST API both available through PyPI and still included in
default installation.


Shuup 1.9.13
------------

Released on 2019-11-12 11:15am +0200.

Core
~~~~

- Add default to order line modified on migration

General
~~~~~~~

- Adjust django-filer version for Django 1.8 and 1.9

Tasks
~~~~~

- Fix issue with broken div in dashboard item


Shuup 1.9.12
------------

Released on 2019-11-07 2:40pm +0200.

Admin
~~~~~

- Include breadcrumbs to is active menu check
- Modernize dashboard blocks
- Temp disable home view progress balls as broken
- Fix the initial categories for product edit view 
- Add settings to make select2 fields to load data asynchronously
- Add signal that is triggered when form is valid in views
- Make front url for nav customizable per project
- Show dashboard link at navigation
- Add shop and supplier info to order detail
- Fix issues with order querysets

Core
~~~~

- Move force anons and person contacts to front
- Add orderline behaviour attribute 
- Add related name for shop staff members

General
~~~~~~~

- Move admin and front login forms to settings spec 
- Add shop validation for order printouts


Shuup 1.9.11
------------

Released on 2019-10-18 12:57pm +0300.

Admin
~~~~~

- Init shop product suppliers with only supplier 
- Add option to extend shop edit actions
- Fix bug with supplier create
- Fix the product images management form part

Carousel
~~~~~~~~

- Update max-length for slide external URL

Core
~~~~

- Add slugfield for supplier
- Allow taxes on order source children lines

Importer
~~~~~~~~

- Allow to use custom file_transformer

Notify
~~~~~~

- Fix z-index on the modal-dialog


Shuup 1.9.10
------------

Released on 2019-10-02 5:00pm +0300.

Admin
~~~~~

- Add option to add messages menu entries
- Orders, fixed `self.request.shop` to `get_shop(self.request)`
- Fix issues with product list mass actions
- Fix /sa/ products mass-actions
- Make the refund lines data be an object instead of an array
- Add tests around refund view
- Add suppliers to product list by default
- Hide arbitrary refund option when disabled
- Highlight active items on menu
- Add object saved signal with request for logging
- Add option to register log menu entries

Core
~~~~

- Add order line creation and modification dates
- Allow refunding other than product lines 
- Add the parent line supplier in the refund supplier line
- Add SHUUP_ prefix to settings
- Add SHUUP_ prefix to ALLOW_ARBITRARY_REFUNDS-setting
- Add option to disable arbitrary refunds
- Do not try to refund lines without quantity
- Fix issue with order source update from order

GDPR
~~~~

- Add 3 years on GDPR consent cookie expiration date
- Add templatetag function to return all the cookies consented
- Add default active field to allow default checked cookies

Notify
~~~~~~

- Create environment provider method set through settings
- Fix the email template variable name
- Add option to wrap HTML body
- Define script log entry
- Make it possible to change the event runner 
- Make it possible to use from_email when sending emails

Utils
~~~~~

- Add force text for value to models get data dict

XTheme
~~~~~~

- Add option to skip resource injection 


Shuup 1.9.9
-----------

Released on 2019-08-21 9:30pm +0300.

Admin
~~~~~

- Add option to pass extra dropzone configurations to widget
- Add option to soft delete CMS pages
- Add option to soft delete suppliers
- Add option to pass extra dropzone configurations to widget
- Fix field help text 

Core
~~~~

- Add option to soft delete suppliers
- Improve filtering for variation children


Shuup 1.9.8
-----------

Released on 2019-08-06 9:00am -0800.

Admin
~~~~~

- Preserve selected section on object edit views
- Update bootstrap colorpicker and change color validation after 1 second
- Update summernote version to latest and enable more editor features
- Fix issues with media browser script
- Fix issue with media dropzone
- Go back to user page after stop impersonating
- Refactor clean method and add test case for inactive user message

Core
~~~~

- Set that contact group shop field can be empty

Front
~~~~~

- Include product image dimensions in Open graph tags
- Refactor clean method and add test case for inactive user message

XTheme
~~~~~~

- Update summernote version to latest and enable more editor features


Shuup 1.9.7
-----------

Released on 2019-06-19 11:15am -0800.

Admin
~~~~~

- Expose dropzone activation to the world 
- Fix boolean test when a false constant is needed
- Fix state issue with order editing
- Customize admin menu with nested levels
- Drop subcategories from admin menu as unused
- Customize admin menu with first level categories

Core
~~~~

- Add signal and notify event when order status changes
- Use force_text in models __str__ method to make sure to return strings

Front
~~~~~

- Filter out invalid suppliers from category list
- Make shipping address optional in checkout phase
- Fix manufacturer, supplier and variation filters


Shuup 1.9.6
-----------

Released on 2019-06-07 11:40am -0800.

Admin
~~~~~

- Fix action button url parse (related to:
  Add default required_permissions to the URLActionButton from url_name)

Shuup 1.9.5
-----------

Released on 2019-06-07 10:00am -0800.

Admin
~~~~~

- Add default required_permissions to the URLActionButton from url_name
- Fix contact & order address form breaking on region copy
- Edit Supplier description as HTML-field. This requires that you mark
  supplier description safe when rendering.

Core
~~~~
- Enable image upload for Categories through REST API
- Add basic REST API to for contact groups and contact group display options
- Add custom template tag to render static source urls. The template tag adds
  the Shuup version as a suffix to burst caches
- Fix compute bought with relation algorithm. Relate products directly and
  render parents in cross sell plugins when configured to
- Fix Contact field to use a field that considers django polymorphic.
  Original JSONField has a bug that doesn't consider Django polymorphic
  environment and fail to deserialize the value.

Front
~~~~~

- Do not render bought with relations with siblings
- Only show marketing permissions check on first checkout. Save a
  configuration for each customer inside the options field
- Add selected for complex variations and tests
- Improve front filters JS customisation
- Add missing data- attribute with the product ID. When product was not
  orderable, the template rendered didn't contain the correct product id
  making the product images disappear.
- Add custom event to warn that product list has been loaded
- Replace Xtheme products view with all category view
- Make sure to get unique product ids when computing relations. Without that
  the same product could run many times wasting time and resources
- Select variation children in product detail view. Make the simple variation
  option selected in parent product detail view
- Fix pagination by adding default page number and clearing the loading state
- Remove extra div tag
- Fix rendering problem with purchased files
- Add custom field ids format to prevent duplicates 

GDPR
~~~~

- Do not ask to consent documents already consented
- Make consent checkboxes optional for auth. This is choice the merchant can
  make from admin panel. By default all consent checkboxes are enabled.


Shuup 1.9.4
-----------

Released on 2019-05-14 4:15pm -0800.

Admin
~~~~~

- Add option to setup auto reload for page
- Show name for active supplier at all times when multiple suppliers are
  enabled for Shuup project (refs to `shuup.admin.supplier_provider:get_supplier`.
- Bump shop product cache on supplier save
- Enable manufacturer logo for APIs
- Adjust refund view for supplier

Core
~~~~

- Add options JSON field for `shuup.core.models.Contact`.
- Do not allow creating payment when the not paid amount is not valid
- Expose data from `shuup.core.order_creator.SourceLine`

Front
~~~~~

- Pass down the supplier in product macros
- Fix issues with supplier in product detail context.
- Pass supplier to orderability check on order form macro
- Improve bootstrap field renderer around multiple checkbox options
- Extend order refund utils for supplier
- Truncate product name to 40 characters in basket partial dropdown
- Go back to old staff user when stop impersonating
- Fix categories product list filter

Miscellaneous
~~~~~~~~~~~~~

- Regions: add Australia to data
- Xtheme: sort plugins by name


Shuup 1.9.3
-----------

Released on 2019-04-22 10:45am -0800.

Admin
~~~~~

- Fix issue with picotable column values 
- Add option to control time step for datetime pickers

Campaigns
~~~~~~~~~

- Fix bug in Campaign free product effect 
- Add campaign supplier to discount lines. When lines causes new lines to 
  basket it is important that those discount lines are linked to correct
  supplier based on campaign.

Core
~~~~

- Fix issues with custom Django User-model
- Include variation parents to bought with calculations

Docker
~~~~~~

- Add new Dockerfile for shuup_workbench

Front
~~~~~

- Fix issue with product images and Simple Lightbox
- Add new products page which shows products for all visible categories. This
  suites fronts that does not have most typical category based navigation
  required.
- Add option to customize customer information forms
- Improve logout when impersonating user
- Make category select for carousel async
- Fix styles for product quantity field at basket
- Improve caches


Simple CMS
~~~~~~~~~~

- Allow page owner see invisible CMS page 
- Add supplier for CMS page


Shuup 1.9.2
-----------

Released on 2019-03-30 17:45pm -0800.

Admin
~~~~~~

- Fix issue with saving default order status
- Improve shipment creation order section and create view
- Add setting to customize datetime pickers format
- Do not collapse attributes product section by default
- Add select2 search inputs min length configurable
- Fix Picotable checkboxes for mobile Safari & improve style
- Add option to extend browser urls through provides
- Fix bug with datetime widgte by making datetime form fields readonly

Campaigns
~~~~~~~~~~

- Add supplier to basket campaigns and to coupon codes
- Enable admin permissions for conditions and effects

Core
~~~~

- Add delete option for product type
- Improve order methods for shipments

Discounts
~~~~~~~~~~

- Add option to limit discounts based on supplier

Front
~~~~~

- Improve sort & filters
- Fix issue with gettext import when gettext is used by addons
- Add option for variation buttons instead select
- Fix bug with variation product orderability check at order detail
- Do not require primary image for product

Notify
~~~~~~

- Improve several issues with admin module styles and fix few issues with
  serializing objects

Simple Supplier
~~~~~~~~~~~~~~~~

- Do not spam spam alert notifications inside a minute
- Make the physical stock be equal to logical when product is not shipped

Miscellaneous
~~~~~~~~~~~~~

- Unlock lxml version limitation
- Update pytoml to toml
- Update Bootstrap outside admin to 3.4.1
- Update Shepherd.js to latest
- Update Parcel bundler to latest version


Shuup 1.9.1
-----------

Released on 2019-03-16 13:30pm -0800.

Admin
~~~~~

- Fix dropzone component and allow browsing local files
- Remove missed message from product view that makes no sense
- Introduce extra permissions for admin modules
- Remove language column from picotable settings

Core
~~~~

- Add managed stock flag in ProductStockStatus
- Add database index for applied attributes fields

Front
~~~~~

- Change templates to not render dashboard links when person is not available
- Add option to explicitly override shop's list sort&filter config
- Make the sort filter data contain the request and current category
- Improve sort and filters to allow hidden fields
- Only set sort & filters data when the form has changed
- Bump sort & filters queryset cache
- Fix custom checkbox rendering for required fields
- Show available date in front template
- Add mixin with fields for base template

Reports
~~~~~~~~

- Fix max and min dates when values are set to None
- Fix start and end date filtering

Xtheme
~~~~~~

- Enable jinja template tags in Snippet plugin

Miscellaneous
~~~~~~~~~~~~~

- Update getting started with development instructions
- Allow all hosts at workbench settings


Shuup 1.9.0
-----------

Released on 2019-02-19 12:00pm -0800.

Admin
~~~~~

- Add documentation for admin modules
- Improve admin module permissions
- Make mass actions extendable
- Enable HTML content in help blocks
- Fix picotable checkboxes breaking the layout
- Add select2 widgets to fetch models async
- Fix Product deletion returning 404

Core
~~~~

- Add labels to order lines
- Add product available until field
- Add extra supplier fields

Discounts
~~~~~~~~~

- Add xtheme plugin to render only products which have discount
- Prevent doing unnecessary joins when fetching discounts

Front
~~~~~

- Multiple bug fixes around sorts and filters
- Improve company registration logic
- Fix issue with image thumbnails
- Improve the way orderability is handled in template tags
- Remove deals only filter from plugins

Reports
~~~~~~~

- Fix excel report writer by forcing strings when writing

Xtheme
~~~~~~

- Change plugins template to render only when products are available
- Create plugin to render a selection of products


Shuup 1.8.2
-----------

Released on 2019-01-11 12:45pm -0800.

Core
~~~~

- Introduce labels for shops and services. Labels can be used to
  group services and shops for multishop/multivendor purposes.
- Introduce order source validator. This enables custom validation
  for very specific cases, such as, customer age check, basket can't
  have a product because customer has some limit to buy it.


Miscellaneous
~~~~~~~~~~~~~

- Front: fix bug in carousel with Firefox and increase padding
  for slide-arrows
- Simple CMS: fix bug in page links
- Addresses: add Croatia to list of EU countries
- Wizard: fix bug in showing field errors at onboarding
- Front: show admin button for all when there is no theme selected
- Admin: fix bug in "save"-button at xtheme edit
- Admin: fix product attribute card on opening
- Admin: Fix bug in order edit view
- Reports: fix bug in report get_totals
- Front: disable "place order"-button on checkout after submit
- Simple CMS: set page availability by default


Shuup 1.8.1
-----------

Released on 2018-12-14 3:45pm -0800.

Fix release for Django 1.8 support.


Shuup 1.8.0
-----------

Released on 2018-12-14 8:45am -0800.

Admin
~~~~~

- Fix dashboard block to include the current shop
  in the queryset
- XTheme: Show guide on theme config page
- Theme editing, remove guide button
- Add option to prevent highlighting a picotable column

Core
~~~~

- Improve to_aware function to consider DST cases
- Add option to pass supplier to pricing context
  for option for supplier based pricing.

Front
~~~~~

- Add supplier is enabled information to supplier
- Add option to remove coupon codes from the basket
- Add option to show and select supplier from front
  when adding products to basket.


Shuup 1.7.3
-----------

- Front: fix bug with re-ordering
- Fix django-parler dependency
- Update Bootstrap version for front to prevent
  vulnerabilities


Shuup 1.7.2
-----------

Released on 2018-11-14 10:30am -0800.

Admin
~~~~~

- Move save button to bottom right corner when not visible
- Move category organizer to addon
- Add option for custom toolbar buttons through provides
- Introduce goto for shopfront

Core
~~~~

- Improve context caches and optimize front queries

Wizard
~~~~~~

- Introduce telemetry wizard step

Xtheme
~~~~~~

- Show editor on popup instead of sidebar

Bug Fixes
~~~~~~~~~

- Admin: Include shop parameter to authentication
- Xtheme: fix plugin form styles
- Admin: Make only active shops visible in search
- Admin: fix order creation errors
- Admin: fix datepicker format
- Front: fix carousel admin
- Admin: fix color widget
- Admin: fix issue with hardcoded menu-toggle URL
- Admin: fix dashboard blocks sort order
- Admin: check whether Masonry can be created before initialize it
- Admin: fix multiple issues with picotable
- Xtheme: fix image plugin by rendering h2 only when necessary


Shuup 1.7.1
-----------

Released on 2018-10-12 8:50am -0800.

Admin
~~~~~

- General fixes to new design
- Fix bug in tour and update to latest shepherd
- Fix bugs in select2 and picotable
- Fix several issues in admin order creator around
  creating orders on mobile device.
- Fix issue in media browser uploads

Front & Xtheme
~~~~~~~~~~~~~~

- Fix bug in sorting placeholders
- Fix image dropzone issue in carousel admin


Shuup 1.7.0
-----------

Released on 2018-10-03 8:25pm -0800.

Admin
~~~~~

- New design and improved usability

Front & Xtheme
~~~~~~~~~~~~~~

- Bug fixes for various features added in
  the latest 1.6.x releases.


Shuup 1.6.16
------------

Released on 2018-09-19 4:45am -0800.

Bug fixes
~~~~~~~~~

- Fix bug in cache signal handler when called through m2m.
  This likely was for Django 1.8 only.
- Front: Include all login form fields on checkout login.


Shuup 1.6.15
------------

Released on 2018-09-14 8:30am -0800.

Admin
~~~~~

- Enable Contact Group Quick add for Contact edit page

Bug fixes
~~~~~~~~~

- Fix ShopProduct & Category ManyToMany relation
- Fix order refund to not adjust stocks when supplier doesn't manage stocks
- Fix product importer to relate the manufacturer to the current shop
- Fix Summernote editing through code view without toggling back to normal view

Xtheme
~~~~~~

- Add Extra CSS/Style class to cells. With snippet tool you can customize
  your content.
- Ask merchant to save plugin when publishing with changes
- Add option to limit category plugin for orderable and discounted
  products only.


Shuup 1.6.13
------------

Released on 2018-09-06 4:45pm -0800.

Admin & Xtheme
~~~~~~~~~~~~~

- Fix bug with Xtheme resource injection

Shuup 1.6.12
------------

Released on 2018-09-06 3:15pm -0800.

Simple CMS
~~~~~~~~~~

- Add option to use custom templates when rendering pages

Bug fixes
~~~~~~~~~

- Fix Xtheme editor menu for mobile devices
- Fix filter fields in order status, simple cms and tasks type admin modules
- Fix GDPR user information serializer to consider the correct document consent structure
- Fix admin wizard skip button alignment

Admin
~~~~~

- Fix bug with stocks in order creator
- Hide menu categories that don't have entries
- Split OrderStatus admin module from Order admin module
- Add option to delete payments from order detail

Discounts
~~~~~~~~~

- Introduce new product discounts with more options, improved discounts admin and
  more efficient performance. You can optionally use `import_catalog_campaigns`
  management command to import old `CatalogCampaign`s.

Core
~~~~

- Enable shop product purchasable attribute and move status text from product
  to shop product. Show product status at the product detail under the basket button.
- Enable context cache to accept string as the item argument
- Add price info cache feature.
- Add SeparatedValuesField to store a list value as a string separated by a character

Classic Gray
~~~~~~~~~~~~

- Improve products card styles to make them align nicely and add carousel for xtheme plugins

Front
~~~~~

- Bump template helpers caches when shop products and manufacturers are saved
- Add edit in admin button to toolbar to enable editing the current object in admin page
- Replace CDN styles with local packages
- Title visibility in CMS pages is now optional

General
~~~~~~~

- Changed the way static resources are built. Parcel is now used to build all apps.

Importer
~~~~~~~~

- Removed shop field from importer form and using the current admin shop

Xtheme
~~~~~~

- Add option to override context for admin. This makes it possible to define
  the logic and which themes are visible for your project.
- Add global snippet injection feature

Shuup 1.6.9
-----------

Released on 2018-08-07 8:15pm -0800.

Bug fixes
~~~~~~~~~

- Fix SampleData admin by adding a `MediaFile` for the shop when creating products sample data
- Fix SimpleSupplier by checking whether the product has sales unit
- Fix product importer to import stocks correctly
- Fix base importer resolve objects method by checking fields existence before querying them

Importer
~~~~~~~~

- Add hook to import images im product importer
- Avoid error 500 when importer goes wrong
- Add special column `ignore` that flags rows to be ignored
- Add option to provide a helper template for every importer.
  The template is rendered in admin when selecting the importer.

Core
~~~~

- Add ``registration_shop`` for ``Contact``.
- Add shop value to ``ContactGroup``.
- Move Price display options to separate object called ``ContactGroupPriceDisplay``.

Admin
~~~~~

- Move Contact Groups menu item under Contacts where it belongs.

Tests
~~~~~

- Tests being run from admin now sets the shop properly to the session. If you
  do not want this, add ``skip_session=True`` parameter for ``apply_request_middleware``.

Campaigns
~~~~~~~~~

- Replace catalog campaigns discount module with `discounts.modules.ProductDiscountModule`


Shuup 1.6.8
-----------

Released on 2018-07-26 10:30am -0800.

Admin
~~~~~

- Make text editor use Shuup media browser when addin pictures

Front
~~~~~

- Fix registration signal to send the person contact
- Make admin toolbar better
- Update Owl Carousel dependency to 2.3.4

General
~~~~~~~

- Unpin Cryptography dependency
- Improve around Django 1.11 support

Simple CMS
~~~~~~~~~~

- Make textarea bigger and resizable

Xtheme
~~~~~~

- Make text plugin to fallback to empty string instead of "None".

Shuup 1.6.7
-----------

Released on 2018-07-16 7:40pm -0800.

Bug fixes
~~~~~~~~~

- Fix to fallback to settings.LANGUAGE when no available language is found
- Fix basket to check whether the payment or shipping method exists before returning it.
- Fix order printouts template by checking whether the addresses are valid
  before calling methods.
- Fix front manufacturer modified filter to consider only visible shop products
- Make Xtheme TextPlugin fallback to empty string when there is no translation for the current language.

Admin
~~~~~

- Make Summernote editor use Shuup media browser when adding pictures.
  Drag/drop and copy/paste were disabled in favor of media browser feature.

Front
~~~~~

- Add option to edit front as anonymous, person or company contact.
- Change the way SVG files are detected in thumnailer. From now on the SVG
  check is done purely based on filename instead of checking the file
  content.

Classic Gray Theme
~~~~~~~~~~~~~~~~~~

- Add option to configure shop logo size styles

Simple CMS
~~~~~~~~~~

- Introduce Xtheme per object layout for pages

Xtheme
~~~~~~

- Make the Parler default language be the first language in plugin multi-language form
- Add option to render extra templates in theme configuration.
- Add option for per object placeholders
- Fix bug deleting last row from placeholder
- Do not render placeholders that can't be edited

Shuup 1.6.6
-----------

Released on 2018-07-06 1:15pm -0800.

Core
~~~~

- Add method to initialize cache variables

Front
~~~~~

- Add parameter to general template tags to filter only products on sale

Xtheme
~~~~~~

- Add option to show only sale items in highlight plugin

Admin
~~~~~

- Add `HexColorWidget` to pick hexadecimal colors on input fields
- Add button to edit selected instances on select inputs

General
~~~~~~~

- Add `front_model_url_resolver` and `admin_model_url_resolver` provides key to resolve models URLs

Carousel
~~~~~~~~

- Add option to customize arrows and slide dot colors

Shuup 1.6.5
-----------

Released on 2018-07-02 1:15am -0800.

General
~~~~~~

- Allow django-mptt<0.9 for Django 1.8 and 1.9.

Shuup 1.6.4
-----------

General
~~~~~~~

- Changed the way regions script is inject into templates.
   Now it is a static source script that can be cached by browser.

Xtheme
~~~~~~

- Add new resource locations: `content_start` and `content_end`

Shuup 1.6.3
-----------

Released on 2018-06-28 8:00pm -0800.

GDPR
~~~~

- When making changes to consent pages, the customer is now being shown (s)he should re-consent.

Core
~~~~

- Add new provider `front_registration_field_provider`.
- Add new provider `front_company_registration_form_provider`.
- Add new provider `checkout_confirm_form_field_provider`
- Add new provider `front_auth_form_field_provider`

Front
~~~~~

- Add shop option to limit storefront language options
- Add option to hide prices and set catalog mode with xtheme settings
- Add new signal `checkout_complete`. Fires when the checkout process is complete.
- Add new signal `login_allowed`. Fires when login allowed is being checked.
- Add new signal `person_registration_save`. Fires when a person registers.
- Add new signal `company_registration_save`. Fires when a company registers.

Campaigns
~~~~~~~~~

- Fix migrations. This would require old projects to fake moved
  `campaigns.0012_basket_campaign_undiscounted` migration.

Importer
~~~~~~~~

- Enable importer modules to provide example files
- Require only shop change permission to execute data imports

Notify
~~~~~~

- Fix migrations. This requires old projects to fake migrations until
  `notify.0006_shop_not_null`.

Simple CMS
~~~~~~~~~~

- Add option to provide form parts to admin edit view
- Add support for choosing whether the timestamps are shown if the
  `list_children_on_page` has been set to `True`.


Shuup 1.6.2
-----------

Released on 2018-06-20 9:30am -0800.

Xtheme
~~~~~

- Fix Finnish translations.


Shuup 1.6.1
-----------

Released on 2018-06-19 13:15am -0800.

Core
~~~~

- Fixed typo on `SHUUP_PROVIDES_BLACKLIST` setting name

Admin
~~~~~

- Do not add or remove superusers from shop staff members
- Fixed shop checkout config to skip form when creating a new shop

Front
~~~~~

- Make company registration per shop
- Add option to enable company tax number validation for EU

General/miscellaneous
~~~~~~~~~~~~~~~~~~~~~

- Add support for Django 1.11 and for now on Shuup is installed over Django 1.11
by default. There is still unofficial support for Django 1.8 and 1.9 which
means that after installing Shuup you can downgrade your Django and Django
polymorphic versions. We will also still run tests for these old versions
while adding new features to Shuup. See tox.ini for information about
downgrades required to run Shuup with old Django.


Shuup 1.6.0
-----------

Released on 2018-06-04 10:15am -0800.

Core
~~~~

- Add Tasks app to manage contact tasks
- GDPR: create option in customer dashboard to download personal data and anonymize account
- GDPR: add xtheme plugin to warn about data protection
- Add models to support General Data Protection Regulation (GDPR)
- Enable creating basket with a custom shop
- Base supplier: Only check stocks for stock managed suppliers when
  creating shipments.
- Make core basket command return the added line id
- Provides: add setting to blacklist undesired provides
- Refund: check the max refundable items when doing partial refunds
- Add customer related fields account manager, tax group and customer
  groups to order for sales reporting.
- Order source: consider the packages quantities in order source lines
- Report: change date filter field to DateTime
- OrderCreator: Dispatch a signal when adding lines to order
- Enable refunds for order API
- API: Improved suppliers stock endpoints
- Add setting to manage contacts per shop
- Add ``ShuupMiddleware`` to set the current request shop
- Add ``get_supplier`` for shop product to define the business logic of
  getting supplier for order/basket line
- Add shops to supplier to define which shops the supplier is available for
- Introduce settings provider through new provide key
  ``shuup_settings_provider``
- Breaking change: Admin Section receives the request object and get methods
  converted to classmethod
- API: allow user to remove and clear basket coupons
- API: allow custom Basket serializer
- API: only return shop products of enabled shops
- Do not allow adding variation parents in the basket
- API: serialize front shop product price info
- API: Return basket customer information
- API: Add option to reset password for authenticated users
- API: Add opiton to reset password with token
- API: ``shuup.front.apps.auth.forms.PasswordRecoveryForm`` to core
- Add name, description and short_description fields to ShopProduct model
- API: add basket endpoint
- API: created front simple product endpoint
- API: add front orders endpoint to fetch users order history
- API: added nearby filter for products
- API: added nearby filter for shops
- API: allow orders to be created without customer, addresses, or service
  methods
- API: add front user endpoint
- API: add address endpoint
- API: add person contact endpoint
- API: add address endpoint

Admin
~~~~~

- Add admin module to configure settings for GDPR
- Add specific form to request and reset staff user password
- Allow shipments only for suppliers assigned to order lines
- Add JavaScript Mass Action type
- Add multi shop support for media browser
- Improve admin order creator translations
- Add option to filter variation parents for product select view
- Fix home view help blocks filtering objects by the current shop
- Fix bug: Filter category parent choices based on current shop
- Add middleware to select and set the current shop in the request
- Breaking change: add optional shop parameter in ``get_model_url`` method of
  admin module
- Add middleware to select the active admin shop using session
- Only categories, orders, products, contacts, campaigns and services for the
  active shop are displayed in the admin
- Menu categories without any children are hidden

Front
~~~~~

- Add custom method to cache MPTT child nodes
- GDPR: require user consent on registration and on authentication
- Breaking change: pass the request from registration views to forms to allow custom logics
- Create GDPR consent when placing the order
- Add shop option to require payment and shipping methods on checkout
- Add shops for carousels
- Add util for checking whether current user is admin
- Limit reqular user login access to own specified shop only

Campaigns
~~~~~~~~~

- Remove uniqueness from coupon code texts. Instead make sure that one shop
  does not have multiple active basket campaigns with same code.

Customer Group Pricing
~~~~~~~~~~~~~~~~~~~~~~

- Introduce Customer Group Discounts.  A discount module to configure
  discounts by contact group.

Notify
~~~~~~

- Add multi-shop support in notify scripts.

Simple CMS
~~~~~~~~~~

- Add page type to support GDPR consent document
- Add shop attribute in `Page` model to work in multishop environments

Importer
~~~~~~~~

- Add multi shop support

Shuup 1.5.0
-----------

Released on 2018-02-22 9:00 +0200.

Campaigns
~~~~~~~~~

- New basket condition and effect for undiscounted items

Reporting
~~~~~~~~~

- Consider timezone in sales report: Localize the order dates to the
  current timezone before using that to group
- Consider timezone in sales per hour report

Tests
~~~~~

- Fix order report tests to use correctly typed datetime parameters

Shuup 1.4.1
-----------

Released on 2018-02-10 14:15 +0200.

Reporting
~~~~~~~~~

- Make selected end date inclusive when filtering orders for reports

Shuup 1.4.0
-----------

Released on 2017-11-29 13:00 +0200.

Admin
~~~~~

- Picotable: Make it possible to provide custom columns

Front
~~~~~

- Category View: Extract product filters to a function

Notify
~~~~~~

- Allow Reply-To header for email notifications

Shuup 1.3.0
-----------

Released on 2017-11-08 12:50 +0200.

Front
~~~~~

- Add SHUUP_CHECKOUT_CONFIRM_FORM_PROPERTIES setting which can be used
  to change confirm form field properties on order confirm page

Shuup 1.2.2
-----------

Released on 2017-11-08 12:35 +0200.

Core
~~~~

- Fix default OrderStatus identifiers and add a management command
  ``shuup_fix_order_status_identifiers`` to fix them in the database too

Shuup 1.2.1
-----------

Released on 2017-10-19 12:30 +0300.

Core
~~~~

- price_display: Fix IndexError when product has no orderable children

Front
~~~~~

- Add missing Finnish translations for customer information app

Notify
~~~~~~

- Serialize Boolean event variable as boolean rather than text

Shuup 1.2.0
-----------

Released on 2017-10-17 15:00 +0300.

Core
~~~~

- Fix caching of price display filters
- Fix serializaiton of JSON fields in Order: Object rather than string
- Add new shipment_created_and_processed signal
- Improve OrderSource caching for deserialization speedup
- Add new product count methods to OrderSource
- Fix bug in purchase multiple checking of ShopProduct
- Add unit interface to ShopProduct, OrderLine and SourceLine
- Add DisplayUnit model
- Rename ``SalesUnit.short_name`` to ``symbol``
- Improve variation product orderability check performance
- Add `created_on` and `modified_on` fields for shop
- Make shop identifier max length to 128 characters
- Add `staff_members` manytomanyfield for shop

Admin
~~~~~

- Fix contact list type filter
- Add option to define a custom admin module loader
- Quick add staff members for shops
- Main menu is now updateable through provides.
- Add new provide category called `order_printouts_delivery_extra_fields`
  which can be used to add extra rows to order delivery slip.
- Add new provide category called `admin_order_information` which can be used
  to add extra information rows to order detail page.
- Use select2 multiple field for shop staff members
- Fix bug in "Select All" mass action
- Fix bug in product choice widget
- Display last 12 months of sales in the dashboard chart

Front
~~~~~

- Add SHUUP_PERSON_CONTACT_FIELD_PROPERTIES setting which can be used
  to change person contact form field properties
- Fix caching of ``shuup.product.is_visible`` template function
- Checkout: Fix method phase attribute population
- Send registration activation e-mail via notify event
- Cusmoter information: Replace untranslated "Not specified" with a dash
- Trigger shipment created event when addons have already processed it
- Fix caching problem related to superuser being all seeing
- Add shop phone and number on order received notification
- Fix bug: Could no change quantities of unorderable lines in the basket
- Use display units when rendering product quantities
- Add new provide category called `product_context_extra`
  which can be used to add extra data to the product context.
- It's now possible to re-order old order from order history
- It's now possible for addons to extend front main menu using the new
  ``front_menu_extender`` provide.  See :doc:`provides.rst` for more
  information.
- Fix default error handler always returning 200 OK as an HTTP status code.
  Now returns the appropriate status code.

Xtheme
~~~~~~

- Revert the query-parameter hack for static files introduced in 1.1.
  Django's ManifestStaticFilesStorage can be used as a cleaner and more
  robust way to implement auto-updating URLs for static files.
- Fix Social Media Links plugin
- Fix product highlight plugin best selling products

Campaigns
~~~~~~~~~

- Fix handling of non-integer quantity in FreeProductLine

Reporting
~~~~~~~~~

- Extend default tax report with pre-tax amount and total

General/miscellaneous
~~~~~~~~~~~~~~~~~~~~~

- Fix usages of non-unicode ``gettext_lazy``
- Improve API documentation of the models with model field descriptions

Shuup 1.1.0
-----------

Addons
~~~~~~

- Enhance/fix bugs addons installation. Addons upload now allows only wheels.

Admin
~~~~~

- Select2Multiple widget now looks for `search_fields` instance attribute to
  get searchable fields
- Allow product variation variables and values to be manually sorted.

Notification
~~~~~~~~~~~~

- Allow user to create scripts based on templates available from
  `notify_script_template` provide category

Campaigns
~~~~~~~~~

- Create Coupons report

Reporting
~~~~~~~~~

- Create Product Total Sales report
- Create New Costumers report
- Total Sales report shows number of customers and the average customer sale
- Create Customer Sales report
- Create Taxes report
- Create Shipping report
- Create Refunds report

General/miscellaneous
~~~~~~~~~~~~~~~~~~~~~

- Add Shuup version to static urls

Shuup 1.0.0
-----------

Core
~~~~

- Add product short description attribute field
- ``SHUUP_REFERENCE_NUMBER_METHOD``, ``SHUUP_REFERENCE_NUMBER_LENGTH``
  and ``SHUUP_REFERENCE_NUMBER_PREFIX`` are now mere defaults and can be
  changed from settings under main menu "Settings > Other Settings >
  System Settings".
- Changed ``SHUUP_REFERENCE_NUMBER_LENGTH`` from 10 to 17
- Add context cache utils. Context cache is mainly build for products and
  shop products but it can cache also other context related content.
- Core: add provide entry to load report writers
- API: add endpoints for product variation management and linkage
- API: add endpoint to make a package Product
- API: add endpoint to add attributes in Product
- API: add endpoint for Product Type
- API: add endpoint to send and manage product media
- API: add endpoint for Attribute
- API: add endpoint for Tax Class
- API: add endpoint for Sales Unit
- API: add endpoint for Manufacturer
- Add option to hide visible categories from menu
- API: add endpoint for Stocks
- Add option to limit service availability with shipping/payment country
- API: Enable option to filter orders with id, identifier, date and status.
- API: Enable option to filter users with id and email.
- API: Add option to filter cotacts with id, email and group id
- API: add endpoint for Shipments
- Add option to limit service availability based on order total
- Add the setting ``SHUUP_ERROR_PAGE_HANDLERS_SPEC`` to handle custom error
  pages (400, 403, 404 and 500)

Admin
~~~~~

- Add shop configuration to only allow orders with a minimum total
- Add order reference number configuration under Shop configuration
- Add System Settings view under "Settings > Other Settings"
- Add option to update order addresses
- Add shop logo block to home page
- Send user confirmation email when new admin users are created
- Add recent orders dashboard block
- Add store overview dashboard block
- Add wizard pane to create shop content pages and configure behaviors
- Picotable now supports related objects. See ``ProductListView`` for example.
- Product list view now lists ``ShopProducts`` instead of ``Products``
- Add variation children to categories from category module
- Set order states manually fom the order detail
- Add FAQ, support, and news/blog dashboard blocks
- Add rich text editor for product, category, and service description
- Add dropzone widget for shop, category, service provider
  and service image fields
- Add option to clear dropzone selection
- Add option to install sample data in Wizard

Front
~~~~~

- ``thumbnail`` template tag now returns SVG images as-is instead of crashing
- Simple CMS and Category views now render metadata based on the description
- Cache template helpers, sorts and filters using context cache
- Enable password reset when shop is in maintenance mode
- Shop can now have a favicon
- Variation children that are not purchaseable should not be visible anymore in dropdowns
- Render product, category, and service descriptions as HTML
- Make carousel slide available by default
- Add dropzone widget for carousel slide images

Xtheme
~~~~~~

- Fix bug: ProductCrossSellsPlugin caused server errors occasionally
- Allow layout to be rearranged in xtheme editor through drag and drop
- Add highlight plugin for category products
- Use rich text editor for text plugin

Campaigns
~~~~~~~~~

- Match child products for parents
- In ``CategoryProductsBasketCondition`` add option to exclude baskets
  containing products from certain categories.
- Add option to select multiple categories to basket condition
- Variation children should match rules based on parent

Simple CMS
~~~~~~~~~~

- Add rich text editor for CMS content


Shuup 0.5.8
-----------

Admin
~~~~~

- Fix bugs in wizard
- Restyle dashboard
- Add option to create categories in product edit

Front
~~~~~

- Fix bugs in rendering address and customer forms
- Add admin link to toolbar

Shuup 0.5.7
-----------

Admin
~~~~~

- Show default image for products without a primary image
- Center the product table image and remove column sort for the image
- Allow product primary image upload from Basic Information section
- Allow multiple file drag-and-drop for product images/files sections
- Add option to skip wizard panes
- Add option to return home view
- List wizard phases at home view


Shuup 0.5.6
-----------

Admin
~~~~~

- Add drag-and-drop support for product image and file uploads


Shuup 0.5.5
-----------

Core
~~~~

- Allow refunding by arbitrary amounts and quantity-only refunds
- Fix bug in ``Order.can_set_complete``
- Currencies can be now created and edited through admin.

Admin
~~~~~

- Some slug fields now auto update their content
- Picotable columns are now orderable
- Simplify product creation
- Make top toolbar fixed
- Refactor menu to allow sub categories
- Make the setup wizard mandatory
- Allow refund quantity/amount to be editable
- Fix ability to add multiple refund lines at once
- Show more details when picking line to refund

Simple Supplier
~~~~~~~~~~~~~~~

- Use shop price properties when in single shop mode for adjustments
  and counts


Shuup 0.5.4
-----------

Core
~~~~

- Telemetry now sends admin email and last login
- Order Statuses are now modifiable through admin.

Admin
~~~~~

- Add help text to product, product type, and category detail/edit pages
- Order creator usability improvements to customer selection
  and quick product addition.
- Ensure `PARLER_DEFAULT_LANGUAGE_CODE` is the first tab in multilingual tab forms
- Show help text as popovers
- Add admin walkthrough


Front
~~~~~

- Add admin toolbar for logged in admins to control product and
  category visibility.

Xtheme
~~~~~~

- Add screenshot support for stylesheets

Shuup 0.5.3
-----------

Core
~~~~

- Products shipping mode is now ``SHIPPED`` by default
- Do not include not shipped products to shipments
- ``OrderSource.language`` is now properly used.
- Start using ``Contact.language``.
  It fallbacks to ``settings.LANGUAGE_CODE`` if not set.
- Add ``SHUUP_AUTO_SHOP_PRODUCT_CATEGORIES`` option that
  allows autopopulating categories. Default is ``True``.
- Populate some unfilled customer fields from order
- Add ``is_not_paid`` function for ``Order`` model.
- Allow zero price payments for zero price orders.

Localization
~~~~~~~~~~~~
- Add Italian translations

Admin
~~~~~

- Standardize picotable datepicker across browsers
- Fix picotable aggregate columns
- Allow setting productless order as completed
- Change main menu template and remove ajax loading from main menu.
- Remove language layer from shop configurations
- Fix bug in product cross-sell editview
- Allow product attribute form extension through provides
- Make form modifiers reusable. Users of ``ShipmentFormModifier``
  should update any references to implement the
  ``shuup.admin.form_modifier.FormModifier`` interface instead
- Add mass actions to products list
- Add mass actions to orders list
- Add mass actions to contacts list
- Picotable lists now support mass actions.
- Add ``PostActionDropdownItem`` baseclass for toolbar so actions requiring
  a POST request do not have to have a toolbar button of its own.
- Add option to set zero price orders as paid without creating a payment manually.

Front
~~~~~

- Basket validation errors are now shown as messages instead of ``HttpResponse 500``.
- Show variation parents in highlight plugins
- Fallback to variation parent image for variation children
  in basket, checkout and saved carts.
- Fix search result styling for products with long names
- Restrict the paginator to show at most five pages
- Enable option to use login and register checkout phases
  with vertical checkout process
- Add checkout view with option to login and register
- Add is_visible_for_user method for checkout view phase
- Add recently viewed products app
- Fix/refactor single page checkout view

Importer
~~~~~~~~

- Remove images from importing products for now.
- Fix `ForeignKey` importing.
- Add `fields_to_skip` for skipping certain items in import.

Shuup 0.5.1
-----------

Released on 2016-10-12 09:30pm -0800.

Core
~~~~

- Fetch support id for shops sending telemetry
- Remove shop languages, category, tax class, service provider and services
  default record creation from ``shuup_init`` management command

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
      front for projects using ``shuup.front``
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

Shuup 0.5.0
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

Shuup 0.4.7
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

Shuup 0.4.6.1
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

Shuup 0.4.6
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


Shuup 0.4.5
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

Shuup 0.4.4
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

Shuup 0.4.3
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


Shuup 0.4.2
-----------

Released on 2016-08-12 03:00pm -0800.

Core
~~~~

- Fix ``FormattedDecimalField`` default value for form fields
- Combine ``TreeManager`` and ``TranslatableManager`` querysets for categories
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

Shuup 0.4.1
-----------

Released on 2016-08-02 07:30pm -0800.

Core
~~~~

- Add ``get_customer_name`` for ``Order``
- Exclude images from product ``get_public_media``
- Add parameter to ``PriceDisplayFilter`` to specify tax display mode
- Add soft deletion of categories
- Add support to sell products after stock is zero
- Fix refunds for discount lines
- Fix restocking issue when refunding unshipped products
- Make payments for ``CustomPaymentProcessor`` not paid by default
- Fix shipping status for orders with refunds
- Fix bug in order total price rounding
- Fix bug with duplicates in ``Product.objects.list_visible()``
- Fix restocking issues with refunded products
- Add separate order line types for quantity and amount refunds
- Add ``can_create_shipment`` and ``can_create_payment`` to ``Order``
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
- Add ``admin_product_section`` provide to make product detail extendable
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
- Add ``StockAdjustmentType`` Enum
- Fix payment and shipment visibility in Orders admin
- Manage category products from category edit view
- Filter products based on category
- Add permission check for dashboard blocks
- Fix required permission issues for various modules
- Make ``model_url`` context function and add permission check
- Add permission check option to ``get_model_url``
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
