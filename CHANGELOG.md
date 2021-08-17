# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

List all changes after the last release here (newer on top). Each change on a separate bullet point line

### Fixed

- Admin: fix typo in product cloner

## [3.1.0] - 2021-08-17

### Changed

- Pull translations from Transifex
- BREAKING: Suppliers with no supplier modules cannot create shipments
- Core: Category.get_hierarchy now ignores any None objects

### Fixed

- Core: fix reindex migration to active the default language

## [3.0.0] - 2021-08-16

### Added

- Core: allow saving encrypted configurations
- Core: add new Catalog API to index and fetch products with annotated price and discounted price

### Fixed

- Admin: do not break when it's not possible to create shipments
- Admin: Fix primary buttons, list buttons, and filter dropdowns to use css variables
- Discounts: show the `exclude_selected_category` field in admin

### Changed

- Admin: Do not let users to set value with decimals while adjusting stock quantity if the sales unit doesn't permit.
- Core: Block an attempt to delete a service provider that still has associated shipping or payment methods.
- Core: consider an order fully shipped only when all out shipments are sent
- Front: improve SEO by tuning description meta tag to product, category and CMS pages
- Importer: index product after importing it
- BREAKING: Core: Discounts are not cumulative anymore. The best discounted price returned by discount modules is considered.
- BREAKING: Discounts: Remove coupon code, availability exception and exclude selected contact group from the Discount model.
  All the related feature were also removed.
- BREAKING: Front: replaced the `ProductListFormModifier.sort_products`
  with a new method: `ProductListFormModifier.sort_products_queryset` and
  removed `ProductListFormModifier.filter_products` and `ProductListFormModifier.filter_products`
  and `ProductListFormModifier.get_queryset`.
- Front: user the new Catalog API on every place that retrieve products from the database
- Xtheme: user the new Catalog API on plugins that retrieve products
- Core: Edit verbose name for ProductMedia.ordering to be more intuitive.

## [2.14.2] - 2021-08-10

### Fixed

- Admin: Fix auth_block macro to have logo as optional parameter
- General: Fix formatted Finish translations

## [2.14.1] - 2021-08-04

### Fixed

- Admin: add `model` attribute to `BaseAdminObjectSelector`
- Admin: Title to use the shop's `requst.shop.public_name` value or `Shuup` as default

## [2.14.0] - 2021-08-03

### Added

- Admin: add new provides `admin_template_injector` that allows injection snippet in admin templates

### Fixed

- Admin: Uploaded shop logo and favicon is updated in admin and auth views

### Changed

- Admin: Overhaul the model selector view in admin to accept generic searches through provides system.
- Admin: Migrate primary, secondary, success, danger, and text color SCSS variables to CSS variables
- Admin: Made active state side menu list icon share same color as text
- Admin: Made the CSS variables stem from initialized Sass variables in Colors object
- Xtheme: Add typography models

## [2.13.0] - 2021-07-27

### Changed

- GDPR: allow provides to extend the user data serialization
- Admin: remove the members field from the permission groups
- Admin: add the groups field in user picotable list
- Admin: improve the format of the user list for mobile devices

### Fixed

- Core: Fix basket quantity for parent package products
- Reports: prevent tables from overflowing to the right in pdf reports
- Core: don't make attribute choices required fields
- Front: enforce setting the current customer to the basket
- Admin: fix crash when viewing an order with a shipment_method without a carrier defined

### Added

- Tasks: trigger a notification event when a task is created
- Admin: add warnings to the product page through provides
- Core: add history for order status changes

## [2.12.0] - 2021-07-15

### Fixed

- Front: SupplierProductListFilter to take all vendors from the category and all sub categories
- Front: Fix the alert class when it is an error
- Xtheme: only use the id attribute if the variable is a Product instance in Async Product Cross Sells plugin
- Reports: do not catch generic `Exception` to prevent hiding other issues

### Changed

- Core: reuse existing `ProductVariationResult` when a combination hash matches

### Added

- Front: add timezone view to save the user's current timezone

## [2.11.0] - 2021-07-07

### Added

- GDPR: create a snippet blocker to prevent injection when cookie is not consented
- Xtheme: create `xtheme_snippet_blocker` provides to allow blocking a global script injection
- Xtheme: add name a `Snippet` object
- Reports: add CSV report writer

### Fixed

- Front: fix so orders that are canceled can't be payed for
- General: fix critical vulnerability on views that were returning not escaped content making it open to XSS attacks
- Admin: fix code mirror destruction by node id

### Changed

- Reports: clean malicius content from the HTML and CSV exporters
- Reports: prevent formulas from being exported in excel writer
- Tests: log errors into a log file
- Admin: hide email template button based on permission
- Reports: improve log when an importer fails

## [2.10.8] - 2021-06-30

### Changed

- Pull translations from Transifex

## [2.10.7] - 2021-06-29


### Changed

- Core: only consider lines from the same supplier as the behavior component


## [2.10.6] - 2021-06-25

### Fixed

- Utils: fix MultiLanguageModelForm so language dependent filed will only be required if the language is required

## [2.10.5] - 2021-06-21

### Fixed

- Xtheme: removed orderable boolean from async highlights plugin from being rendered

## [2.10.4] - 2021-06-21

### Changed

- Admin: show taxless order total column in order list

## [2.10.3] - 2021-06-15

### Fixed

- Importer: fix so the correct context is displayed on first request when selecting importer

## [2.10.2] - 2021-06-11

### Added

- Xtheme: Add so snippets can have start of head content

### Fixed

- Core: fix so task don't require a identifier

## [2.10.1] - 2021-06-07

### Fixed

- SimpleSupplier: always return products as managed by using a different queryset

## [2.10.0] - 2021-06-07

### Removed

- Admin: remove the provides to allow adding extra fields to the Attribute form

### Add

- Core: Allow a supplier to have multiple modules
- Core: add option to store tasks in the database to collect results

### Changed

- General: pull translation strings from Transifex
- Admin: filter products in list and edit views according to product kind listing name
- Core: suppliers don't have default supplier modules anymore
- Importers: enable importers to run asynchronously
- Importers: change the admin views to show the list of import processes

### Fixed

- Admin: fix picotable overflow issue
- Notify: always overrride the current notification data with the new one

## [2.9.2] - 2021-05-26

### Fixed

- General: replace hash() with sha1() as Python's hash() function doesn't have a stable result across processes
- Core: use SHA-1 to hash cache keys as Python's hash() function doesn't have a stable result across processes

### Changed

- Cache product orderability and prices using a list of user groups instead of per contact
- Pull translation strings from Transifex

## [2.9.1] - 2021-05-24

### Fixed

- Admin: add ordering to attribute filter, because of frontend related error

## [2.9.0] - 2021-05-19

### Added

- Admin: add a method in AdminModule that allows returning help texts for permissions

### Fixed

- Notify: add notify styles to the script editor iframe to fix email editor size
- Importer: use more bites in order to detect csv dialect in importer
- Admin: save the current user menu using the current language

### Changed

- Pull DE translations from Transifex
- Xtheme: allow async plugin to have orderable only flag set
- Xtheme: use the current language as part of the plugins cache key

## [2.8.3] - 2021-05-17

### Fixed

- Xtheme: use the context while generating the cache key
- Xtheme: do not crash the whole site when a plugin fails to render
- Admin: Force to parse reason as string before encoding the url

## [2.8.2] - 2021-05-14

### Fixed

- Admin: force escape help texts which can contain `"` characters
- Admin: show translation fields from all polymorphic models available
- Xtheme: hash the cache key to prevent strings larger then 250 chars

## [2.8.1] - 2021-05-11

### Fixed

- Xtheme: encode cache key into base64 to prevent issues with memcache

## [2.8.0] - 2021-05-11

### Changed

- General: make some plugins cacheable
- Xtheme: add attribute on every plugin to indicate whether it can be cached or not

### Removed

- Xtheme: removed the SHUUP_XTHEME_USE_PLACEHOLDER_CACHE setting and do not cache the entire placeholder content

### Fixed

- Core: implement choice attribute getter and setter correctly
- Admin: collect translation strings from Shepard Tour

## [2.7.3] - 2021-05-11

### Fixed

- Admin: use correct translated label syntax for form fields
- Front: Remove untranslated Error! prefix in alert messages
- Campaigns: fix the translation string format

### Changed

- General: use gettext_lazy to make sure translations work
- Front: unify the Customer Information title across the dashboard
- Front: bump bootstrap-select and use translated strings while initializing it

## [2.7.2] - 2021-05-05

### Fixed

- Admin: Fix the Select2 translations strings
- General: Collect translation strings correctly

### Changed

- General: Pull translation strings

## [2.7.1] - 2021-05-04

### Fixed

- Core: do not use message tags as part of the message as it doesn't contain translated string
- Core: fix the python string format syntax to format after resolving the translation string

### Changed

- Settings: add Portuguese (Portugal) as a language option

## [2.7.0] - 2021-04-29

### Added

- Admin: New type of attribute: CHOICES
- Admin: Selection of multiple choices from attribute for product
- Front: Product filter by attribute choices

### Changed

- Pull strings from Transifex

### Fixed

- Reports: convert string into translated string
- Update requirements to support Python3.6+
- Fix mass editing validation for ManyToManyField fields.

## [2.6.5] - 2021-04-22

### Changed

- Front: consider the supplier from context or kwargs while reversing the product url

### Fixed

- Front: Fix the order detail template
- Admin: Pass languages to the TaxClassFormPart to show multilanguage forms

## [2.6.4] - 2021-04-19

### Changed

- Additional German translation strings

## [2.6.3] - 2021-04-13

### Changed

- Update German translation strings

## [2.6.2] - 2021-04-13

### Fixed

- Front: pin LESS version to prevent build breaks

## [2.6.1] - 2021-04-13

### Changed

- Front: add extra head block to base template
- Core: allow refunds creation when the order is complete
- Admin: show the product picture in order item list
- Admin: change so TaxClassEditView is a FormPartView
- Admin: Picotable to scroll in container on overflow rather, than entire screen scroll

### Fixed

- Front: Fix error that occurred while trying to register as a company
- Front: fix non existent macro import
- Core: Fix error that occurred when creating an order with a product which SKU was longer than 48 characters.
- Admin: Multiple duplicate images being saved when image is uploaded before product is saved

## [2.6.0] - 2021-03-29

### Changed

- Admin: Improve the copy product functionality

### Added

- Admin: add number of received orders in orders menu
- Admin: add contact CSV exporter
- CORE: Add .jsx support for shuup_makemessages command

### Fixed

- Admin: prevent exporting products that are not accessible by the current user
- Fix 'Customize Your Admin Menu' redirecting to the supplier specific edit page on saving.
- Admin: Fix picotable mobile styling to default to full-width
- Front: Fail cleanly when visiting a product page without supplier
- Fix Docker build issues with the development compose file.

## [2.5.0] - 2021-03-22

### Changed

- Front: Add so `basket.get_final_lines(with_taxes=True)` gets called after selecting shipping- and payment method.
  Reason for this is so all the taxes gets calculated before end customers fills in their payment details
- Core: undeprecate signals for ShopProduct model

### Added

- Core: add attribute in Carrier model to control whether to manage shipments using default behavior
- Admin: add shipment list view to list all shipments

### Fixed

- Notify: Fix so there is no 500 error when accessing EmailTemplate settings page
- Taxes: fallback location to billing address when shipping address is not available
- Importer: Ignore rows without any data

## [2.4.0] - 2021-03-02

### Added

- Admin: add option to hide font selection and always paste plain text in summernote editors

### Changed

- Core: move refund order line logic to tax module
  - Since each refund line you need to take care of the taxes it is
  more logical if the tax module handles the whole thing. With some
  3rd party taxation tool you need an option to handle refund taxes
  in different way.

### Fixed

- Added missing labels to product category and supplier fields

## [2.3.18] - 2021-03-01

### Added

- Front: create shipment sent notify event
- Core: add shipment tracking url to shipment model
- Admin: add shipment action to mark a shipment as sent

### Changed

- Admin: fix product module not to fail on object does not exists
- Front: update media upload URL from "media-upload/" to "upload-media/"
- Core: bump attribute name to 256 characters

## [2.3.17] - 2021-02-23

### Fixed

- Core: Adding normal products with only deleted children to basket

### Removed

- Front: remove templatecache around basket partial as not stable with custom baskets

## [2.3.16] - 2021-02-18

### Fixed

- Xtheme: fix wrong queryset that was fetching different products from the selection

## [2.3.15] - 2021-02-17

### Changed

- Admin: Disable scrolling on jquery datetime pickers
- Core: Turn variation parent mode back to normal if it has no non-deleted children
- Core: add cached property groups_ids for Contact
- Core: add lru_cache to display unit
- Core: make some Contact properties cached
- Front: optimize queries for orderable variations fetch
- Core: set shop and product for shop instance to prevent query
- Front: prefetch sales units for category view
- Lock cryptography version for test builds
- Use shop instead theme settings shop when initializing theme
- Xtheme: save current theme to request for later usage
- GDPR: add lru_cache for shop_setting getter

### Fixed

- Admin: fix bug in user permission view
- Do not rely on STATIC_URL and MEDIA_URL while formatting static and media urls

## [2.3.14] - 2021-02-04

- Front: add template cache to basket partial
- Core: avoid unnecessary touching to basket customer …
- Core: cache basket attributes while get and add cache key attribute …
- Front: skip front middleware for static and media
- Core: add makemessages support for do and cache templatetags
- Update license header for 2021

## [2.3.13] - 2021-01-28

### Added

- Admin: Add an open/close all groups button to 'Granular Permission Groups' list.

### Fixed

- Admin: Update styling for media browser
- Admin: Ensure media browser images are squares without cropping
- Xtheme: fix sortable import for static resources
- Admin: Gracefully handle the error when trying to delete a PROTECTED MediaFolder.

## [2.3.12] - 2021-01-26

### Added

- Setup: add .html to MANIFEST.in
- Admin: Add text truncate CSS to user dropdown if the user's username
  gets too long and display only a user icon on mobile screens
- Admin: always display the dashboard link in the main navigation as the first item
- Save basket just before starting the order creation.
  This ensures we have latest basket there on store
- Save basket after shipping or payment method is saved.
- Save basket after shipping or billing address is saved. For
  saving the addresses to basket data
- Add option to add log entries linked to stored baskets
- Add detail page for carts

### Changed

- Admin: Change visit shop link from an icon to a button with text
- Hide "finished" carts by default
- Modify carts list to show latest cart first

### Removed

- Admin: Remove dashboard and home icon links from top menu
- Remove the delay filter as useless. No need to hide carts

## [2.3.11] - 2021-01-25

### Added

- Core: add verbose_name to shop product so we can translate it
- Core: add middleware provides to the basket command handler
- Core: add provides to retrieve properties from order or order source
- Front: render subscription options in basket template
- Core: add provider to retrieve subscription options for a given product

### Changed

- Front: render basket and order line properties using the `front_line_properties_descriptor` provides
- Admin: change the product files form part icon to a file icon
- Core: cache language utils methods using LRU

## [2.3.10] - 2021-01-22

- Notify: make email template form use code editor with preview
- Notify: make email action body use code editor with preview
- Admin: add code editor with preview widget
- Notify: Remove breadcrumbs from editor and add save button on top
- Notify: make editor close button to Close instead Done
- Add related name to package links to enable better queryset performance
- Ensure migrations are fine for longer log entry fields

## [2.3.9] - 2021-01-19

### Changed

- Admin: add UX improvements through small style updates

### Fixed

- Admin: add apply filters button and display active filters counter badge
  - Do not save and refresh Picotable lists on filter change, but wait
  that the user selects the "Apply filter" option. Also show badge for
  active filters to indicate that some content is filtered out.
  Consider "_all" as not filter.
- Xtheme: fix summernote icons by using the original summernote css file

## [2.3.8] - 2021-01-13

- Front: fix with the product images on price update
  - patches previous v2.3.7 release

## [2.3.7] - 2021-01-12

- Front: improve async product carousel breakpoints
  - Also add option to easily override breakpoints by
    re-defining the breakpoint variable.
- Front: optimize child product orderability checks a bit
- Front: add option to replace product detail context
- Front: optimize rendering images for variation products
- Core: optimize price range calculations

## [2.3.6] - 2021-01-08

### Added

- Admin: add mass action to send password reset emails to selected users
- Notify: send notification when user request to reset password
- Core: remove the dependency of shuup.notify while resetting user's password
- Core: add signal that is triggered when user request a password reset email

## [2.3.5] - 2021-01-07

- Core: unify tax number max length at models
  - Also good practice would be not to validate tax number
  on model level but instead at the form since tax number
  format varies per country/region.

## [2.3.4] - 2021-01-06

### Changed

- Xtheme: use the shop provider instead of falling back to first shop
- Admin: cache the user permissions in the user object
- Admin: make shop provider cache the shop in the request
- Xtheme: add option to disable placeholder cache
  - Use setting SHUUP_XTHEME_USE_PLACEHOLDER_CACHE = True for this

### Removed

- Core: remove GB from countries in European Union


## [2.3.3] - 2021-01-05

- Patches v2.3.2 a bit around the xtheme editing

- Xtheme: add Jinja markup in custom snippet type


## [2.3.2] - 2021-01-04

### Changed

- GDPR: hide consent immediately on accept
- Notify: Make HTML default format for emails
- Improve the way the cache is bumped when order is created and changed

### Fixed

- Admin: fix missing `tr` closing tags

### Removed

- Notify: Remove HTML editor from notifications since summernote does not
function Jinja syntax very well and for example for-loops and ifs
cause easily broken notifications.


## [2.3.1] - 2020-12-28

### Changed

- Admin: MultiselectAjaxView returns ordered by name choices

### Fixed

- Fix `0068_help_text_improvements` migration file to have the correct field char size: 128
- Fix _vertical_phases.jinja incorrectly targets all forms
- Fix initial value of Choose to register form

## [2.3.0] - 2020-12-16

### Added

- Dashboard: Sorting of dashboard items by ordering number
- Xtheme: add option to set a custom cell width in placeholders

### Changed

- Admin: set product default price value initial value to zero

### Fixed

- Admin: Fix multiple translations returned when using values_list on translated field
- Front: Fix so mass and measurements unit is displayed in same unit as in the backend

### Removed

- Product variation management. [Use this instead](https://pypi.org/project/shuup-product-variations/).

## [2.2.11] - 2020-12-08

### Fixed

- SimpleCMS: Show all CMS pages for authenticated users
  when there is no group filter attached to the page

## [2.2.10] - 2020-12-04

### Fixed

- GDPR: do not create consent for anonymous user in checkout


## [2.2.9] - 2020-11-23

### Changed

- Core: Increase field lengths in *LogEntry models
  - Add an index to the indentifier for faster querying.
  - Use the same error prevention measures for message than is done for
    identifier in _add_log_entry() for consistency.

### Fixed

- Core: Fix `ProtectedError` when deleting a `Manufacturer` which was still
  connected to product(s).


## [2.2.8] - 2020-11-23

### Added

- Add font size 16 to summernote text editor

### Fixed

- GDPR: make sure to return a blank list in the `get_active_consent_pages`
  method when there is no page to consent


## [2.2.7] - 2020-11-20

### Fixed

- Admin: do not add/remove shop staff member while saving a staff user


## [2.2.6] - 2020-11-17

### Added

- Include products belonging to child categories of filtered category

### Changed

Admin: do not allow non-superusers manage superusers
  - Do not show is_superuser field for non-superusers no matter
    who they are editing
  - Do not show superuser column in list since the superusers are
    already filtered out from non-superusers who are main people
    using the admin panel.


## [2.2.5] - 2020-11-12

### Fixed

- Front: force recalculate lines after setting the payment and shipping methods to the basket in checkout phase

### Changed

- Don't display taxless price when it's equal to taxful in checkout

### Added

- SimpleCMS: Add field to limit a page availability by permission group

## [2.2.4] - 2020-11-09

### Fixed

- Core: Fix basket implementation that was using the same memory
object for all baskets instances in the same process

## [2.2.3] - 2020-11-05

### Fixed

- Add missing id field to the media forms


## [2.2.2] - 2020-11-03

### Fixed

- Prevent duplicate images in product media form
- Do not render duplicate hidden media form field


## [2.2.1] - 2020-11-02

### Changed

- Update French, Finnish and Swedish translations
- Change the Supplier.objects.enabled() filter to only return approved suppliers

### Changed

- Admin: Show a loader in place of picotable when a request is pending.

## [2.2.0] - 2020-10-23

### Possible breaking change

- When updating to this double check your project filters around supplier are working
  after this Supplire shop->shops change.

### Changed

- Admin: change the supplier views to update the approved flag for the current shop only
- Core: change the Supplier object manager to consider the approved flag for the given shop

### Added

- Core: add new module SupplierShop to store thre M2M relationship between the supplier
and the shop with additional attributes

## [2.1.12] - 2020-10-21

### Fixed

- Importer: fix the product importer to prevent parent sku being the current product or other variation child

## [2.1.11] - 2020-10-15

### Added

- Add Spanish and French (CA) translations from Transifex
- Notify: Add a new `attributes` attribute to `shuup.notify.base.Variable` for showing examples
  of which attributes can be accessed in the script templates.
- Notfiy: Show some `Order` related attributes in the notify templates.

### Fixed

- Core: include arbitrary refunds for max refundable amount
- Admin: select product variation in popup window
- Importer: ignore None columns while importing files
- Admin: Show more descriptive error messages in the media uploader in some situations.

### Changed

- Update Finnish and Swedish translations from Transifex
- Importer: add option to import product variations
  - Add option to import product variations
  - Improve handle stock to get supplier by supplier name and
    set the supplier stock managed and update the module identifier.
  - Improve handle stock to set the logical count to desired quantity
    instead adding new stock for the amount. This should help sellers
    to keep their product stock value correct.
- Preserve newlines in vendor and product descriptions even when
 `SHUUP_ADMIN_ALLOW_HTML_IN_PRODUCT_DESCRIPTION` and `SHUUP_ADMIN_ALLOW_HTML_IN_VENDOR_DESCRIPTION` are `False`.
- Importer: log errors in the importer and use specific exception classes instead of using Exception
- Notify: make the default script language be the fallback from Parler
- Admin: Hide the 'Root' folder from users that do not have the `"media.view-all"` permission.


## [2.1.10] - 2020-09-29

### Fixed

- Front: fix typo in pagination

### Translations

- Update Finnish and Swedish translations


## [2.1.9] - 2020-09-23

### Fixed

- Fix button that removes coupon from the basket by using the correct JS event property

## [2.1.8] - 2020-09-15

- Update translations strings
- Importer: fix product CSV importer to better match the headers


## [2.1.7] - 2020-09-11

- Admin: improve product variation management. This release purely
  amends release 2.1.6.


## [2.1.6] - 2020-09-11

Admin: add supplier check to product list and edit views
Admin: improve product variation management

  Remove activate template form field as confusing.

  1. Now when add new template:
    - New empty template is created

  2. When you have template selected:
    - Product variations are saved based on the form
    - Variation options are updated to the selected template

  3. When template is not selected:
    - Product variations are saved based on the form


## [2.1.5] - 2020-09-08

### Fixed

- Requirements: require Markdown>=3,<4 instead <3
- Xtheme: Fix social media plugin form initial data population.


## [2.1.4] - 2020-09-08

### Fixed

- Xtheme: fix social media plugin form populate
- GDPR: Fix anonymization error when an order of a contact had no shipping or billing address.


## [2.1.3] - 2020-08-28

### Fixed

- Xtheme: fix model choice widget for plugins (django 2)


## [2.1.2] - 2020-08-26

### Fixed

- Xtheme: fix editor template issue
- Simple CMS: make sure to pass optional parameters through kwargs in form


## [2.1.1] - 2020-08-26

### Added

- Admin: add option to delete attributes

### Fixed

- Xtheme: fix editor template issue and make sure to pass optional parameters through kwargs in form
- Notify: unescape email subject and body to prevent sending broken characters in emails


## [2.1.0] - 2020-08-24

### Added

- shuup.notify: add notification_email_before_send signal to SendMail
- shuup.notify: add event identifier to Context


## [2.0.8] - 2020-08-24

### Fixed

- Prevent crashing when trying to cache an unpicklable value.


## [2.0.7] - 2020-08-21

### Fixed

- Fix passing a `reverse_lazy()` URL as the `upload_url` argument for `FileDnDUploaderWidget`.


## [2.0.6] - 2020-08-18

### Changed

- Admin: Make the order editor keep the suppliers of non-product order lines intact.

### Fixed:

- Admin: Fix the edit button on the order editor.


## [2.0.5] - 2020-08-16

### Added

- Admin: user and permission based access to media folders

  This means that all vendors can have their own root folder and do what every they want in that folder.
  But it also allows the admin to give viewing access to one folder for all suppliers.


## [2.0.4] - 2020-08-07

- Testing: add missing migrations


## [2.0.3] - 2020-08-07

- CMS: add missing migrations


## [2.0.2] - 2020-08-07

### Changed

- Removed Django 1.11 compatible code from the code base

### Fixed

- Admin: fix logout view that was loading the template from Django instead of custom template
- Admin: return `None` when the order source was not correctly initialized in JsonOrderCreator
- Core: add parameter in shuup_static to load the version of a given package


## [2.0.1] - 2020-08-04

- Add initial support for Django 2.2


## [1.11.10] - 2020-08-04

- Fix issue on arranging menu after reset which sets the configuration None
  which in the other hand is hard to update as it is not dict.


## [1.11.9] - 2020-08-04

- Admin: add option to arrange menu for superuses, staff and suppliers

  For now it was only possible to arrange menu per user which is not
  sufficient while the menu needs to be arranged for the whole group
  of people like shop staff or vendors.

  Allow to create menu custom menu for superusers, staff or suppliers,
  but remain the possibility to still arrange the menu per user.

  Add option to translate each menu arranged for these groups since
  not all vendors/suppliers necessary speak same language.


## [1.11.8] - 2020-07-31

### Fixed

- Fix admin order edit tool to use correct id for supplier query
- Admin: limit the Manufacturer delete queryset per shop

### Added

- Notify: added email template object to store reusable email templates for SendEmail actions
  This contains a migration step to move all old body template field to use email templates.

### Changed

- Xtheme: move CodeMirror JS lib dependence to Admin
- Sanitize product description on save if `SHUUP_ADMIN_ALLOW_HTML_IN_PRODUCT_DESCRIPTION` is set to `False`

## [1.11.7] - 2020-07-23

### Added

- Core: Add dynamic measurement unit system
  - New settings for specifying units:
    - `SHUUP_MASS_UNIT`
    - `SHUUP_LENGTH_UNIT`
  - New function for getting the volume unit: `shuup.core.utils.units.get_shuup_volume_unit`

### Changed

- **BREAKING**: Change `Shipment` default weight unit from `kg` to `g`
- **BREAKING**: Change `Shipment` default volume unit from `m3` to `mm3`
- **BREAKING**: Change `ShipmentProduct` default volume unit from `m3` to `mm3`

### Removed

- Remove 'known unit' validation from `MeasurementField`, it can contain any units now

## [1.11.6] - 2020-07-22

### Changed

- Front: Add priority attribute to base order form to enable using precedence

## [1.11.5] - 2020-07-07

### Added

- Add signal when an email is sent by a notification

## [1.11.4] - 2020-07-06

- Fix issue with browser tests

## [1.11.3] - 2020-07-04

### Added

- Add `Dockerfile-dev` for development
- Add Docker instructions to docs

### Changed

- Add theme for the shop in `shuup_init`
- Make the shop not be in maintenance mode in `shuup_init`
- Make `Dockerfile` use `shuup` from PyPi for faster build time

## [1.11.2] - 2020-07-03

- Move workbench sqlite database location for upcoming Docker setup

## [1.11.1] - 2020-07-03

### Added

- Admin: Add settings for controlling allowing HTML in product and vendor descriptions


## [1.11.0] - 2020-07-02

### Changed

- Importer: add context object while initializing a importer class
- Core: use UUID in basket IDs to prevent possible duplicates
- Core: save basket shipping and billing address as dictionary when id is not available
- Front: remove the custom _load() implementation from the basket as it is the same as the core
- Core: ignore lines that are not from the given source while calculating taxes
- Campaigns: do not apply campaigns in baskets configured to a supplier
- Admin: change service admin to list only providers that the current user can access
- Use UUID4 while generating order line ids by default
- Admin: Improve message banners, by:
    - Resetting the timeout for hiding the messages when a new message is added.
    - Immediately clearing the already hidden messages a when new one is added.
    - Not hiding messages when clicking just random background elements.
    - Allowing dismissing all of the messages by clicking any one of them anywhere.

### Added

- Admin: add improved product copy
- Core: add task runner to support running tasks using 3rd party services like Celery
- Core: add shops and supplier to ServiceProvider and Service models
- Front: add feature for checkout phases to spawn extra phases
- Add custom get_ip method and use it everywhere
- Importer: add permissions for all the diffrent types of importers
- Importer: add context class to data importer

### Removed

- Travis jobs for Django 1.8 and 1.9

### Fixed

- Removed the kind prefix from feedback messages using Django messages to prevent duplicate strings.
- Fixed the way the permissions identifier are split in admin
- Fixed issue that was importing User model directly
- Core: changed `del` basket command handler to not try to parse the basket line into an integer


## [1.10.16] - 2020-06-03

- Simple CMS: Fix a bug with the page links plugin

## [1.10.15] - 2020-06-02

### Changed

- Front: Ensure company name and tax number is set to both billing and shipping address same way
as when filled through company form when customer is not logged in. Company name and tax number
at order addresses seems to help with some taxation logic as well as makes things more consistent.

### Fixed

- Admin: Make sure related custom columns are added accrodingly. Fix issue with filtering through columns
that are by default hidden

## [1.10.14] - 2020-05-27

### Fixed

- Front: only show carousel title when there is one

### Changed

- Notify: Add AccountActivation event. AccountActivation event is
  triggered only when the user is activated for the first time.
- Front: improve next parameter with registration. Check GET
  parameter first and then fallback to POST data.

## [1.10.13] - 2020-05-20

- Admin: fix width issue with picotable images
- Admin: fix bugs in order edit and improve it one step closer to
  multivendor world. Now supports situation when vendors does not
  share products.
     - Add option to make shipping and payment method optional
     - Add supplier to pricing context
     - Show supplier name on product column
     - Make auto add for product select false by default
     - Fix product select2 missing URL and data handler since
       the whole ajax method was passed as attrs.
     - Add option to open/close collapsed content sections in mobile
- Core: add option to enable order edit for multiple vendors
- Front: do not stack history on product list when filters are changed.
  Instead replace state so back-buttons works nicely.
- Front: prevent image Lightbox touching history so you do not need
  to click back 6 times after you have viewed all images.

## [1.10.12] - 2020-05-05

### Added

- Admin: add error message when upload fails. At media queue complete do not
  resave product media if the file-count has not changed. This for example
  prevents media save when the upload itself fails.
- Admin: add option to override dropzone upload path by using data attribute
- Admin: add upload path to browser URLs and use it to fallback on media
  uploads when the actual media path is not available.
- Admin: Ability to delete manufacturer
- Admin: Ability to login as the selected contact if it's a user

### Fixed

- Admin: Now when activating/deactivating user it's contact will also change
- Admin: New notification for when a account get's reactivated

## [1.10.11] - 2020-04-23

### Fixed

- Discounts: create different admin module for archived discounts to fix breadcrumbs
- Fix product pagination by not overriding the state with undefined values

### Fixed

- Middleware: fix so it trys to take the users timezone first, then the suppliers, last the projects TIME_ZONE

### Changed

- Front: customize sort options through settings

## [1.10.10] - 2020-03-24

### Fixed

- Admin: Notification name when deleteing it
- Admin: Update contact list so that it only shows customers by default
- Front: Fix typo

### Changed

- Front: Add supplier choice to best selling product context function
- Admin: allow sorting categories by name
- Admin: show product orderability errors as list


## [1.10.9] - 2020-03-24

### Fixed

- Admin: remove pinned /sa/ URL from scripts to support dynamic admin URLs
- Admin: Fix graphical (incorrect indent) bug in Product / Stock Management

## [1.10.8] - 2020-03-20

### Changed

- Admin: add spinner and progressbar options components through Bootstrap 4.

### Fixed

- Issue running category filter browser test with Travis


## [1.10.7] - 2020-03-09

### Fixed

- Admin: remove pinned /sa/ URL from scripts to support dynamic admin URLs
- Front: keep the current query string parameters as the initial state
  when refreshing product filters.

### Changed

- Admin: fix page jumps after reaload
- Admin: make browser urls support urls with parameters

## [1.10.6] - 2020-02-28

### Changed

- Core: supplier name max length to 128 from 64

## [1.10.5] - 2020-02-27

### Added

- Add option to send notification event at password recovery

### Changed

- Improve the admin modals to use flexbox and work better on small devices

### Fixed

- Admin: fix password recovery success URL
- Picotable: render the filters button on small devices,
  even when there is no data, to allow resetting filters

## [1.10.4] - 2020-02-22

### Changed

- Make Admin messages dismissible

### Fixed

- Admin: Fix search results overflowing the canvas

## [1.10.3] - 2020-02-21

### Fixed

- Admin: fix bug when uploading product media

## [1.10.2] - 2020-02-19

### Added

- Admin: add option to impersonate staff users
- Notify: add option to delete notify scripts
- Admin: Allow shop staff to impersonate regular users
- Notify: Add BCC and CC fields to SendEmail notification action.
- Add the CHANGELOG.md to the root of the code base.

### Changed

- Xtheme: Improve template injection by checking not wasting time invoking regex for nothing
- Add `MiddlewareMixin` to all middlewares to prepare for Django 2.x
- Notify: Changed the Email topology type to support comma-separated list of emails when using constants.
- Front: skip product filter refresh if filters not defined
- GDPR: change "i agree" button to "i understand"

### Fixed

- Front: fix notification template default content
- Admin: improve primary image fallback for product
- Fixed the placeholder of Select2 component in Admin
- FileDnDUploader: Add check for the `data-kind` attribute of the drop zone. If the data-kind is
  `images`, add an attribute to the hidden input that only allows images to be uploaded.
- Front: fix bug with imagelightbox
- CMS: Free page URL on delete

## Older versions

Find older release notes [here](./doc/changelog.rst).
