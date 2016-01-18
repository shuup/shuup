Shoop Change Log
================

Unreleased
----------

- List all changes after last release here (newer on top).  Each change on a
  separate bullet point line.  Wrap the file at 79 columns or so.  When
  releasing next version, the "Unreleased" header will be replaced with
  appropriate version header and this help text will be removed.

- Remove AddressManager
- Split address into mutable and immutable address

Version 2.0.0
-------------

Released on 2015-10-05 16:45 +0300.

The highlights of this release (over 500 commits since 1.2!) are:

- Revamp of the pricing and taxation systems for flexible international
  commerce
- A new pluggable frontend theming system called Xtheme
- Usability improvements for the admin, including much better media
  management
- A brand new, slick frontend theme "Classic Gray"
- Lots and lots of other fixes and improvements!

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


Version 1.2.0
-------------

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


Version 1.1.0
-------------

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

  - It now lives in https://github.com/shoopio/shoop-stripe

- Core: Declare correct ``required_installed_apps`` in AppConfig

- Fix handling of tuple-format ``required_installed_apps``

- Fix Money class to not read settings at instance creation

- Fix management command ``shoop_show_settings`` for Python 3

- Add Addon documentation (doc/addons.rst)


Version 1.0.0
-------------

Released on 2015-06-04 16:30 +0300.

- The first Open Source version of Shoop.
