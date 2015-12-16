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

- Revamp of the pricing and taxation systems for flexible international commerce
- A new pluggable frontend theming system called Xtheme
- Usability improvements for the admin, including much better media management
- A brand new, slick frontend theme "Classic Gray"
- Lots and lots of other fixes and improvements!

Admin
~~~~~

- Add basic Manufacturer views (914d456)
- Basic Supplier management (65787f3, 3953e24, b864e27)
- Add image field for category (9157b26)
- Fix issue with price not being saved (eb90ff5)
- Optionally disable creating shops (f427f6a)
- Add `Product Media` tab to product editing (279a26d)
- Tabify translated fields (46b49c5)
- Variation UI styles (bf5a9ba)
- Media Browser Rehaul (9f4ff68, b7b3d39, 35e4354, 1d22009, 4c4345f)
- Add `ImageChoiceWidget` (7548fb5)
- Admin: Actually send `data-filter` to media browser from browse widgets (cca4a57)
- Admin form error indicators (b13a4c3)
- Add keyboard shortcuts to megasearch (d5c75dc)
- Show first language tab with errors (a3c1fd0)
- Update styles for admin form error indicators (00c644d)
- Show errors more clearly (7a8620b)
- Make folder clicks work at media browser (d66954b)
- Fix paths of generated source maps (3a738ce)
- Add styles for bootstrap input-group (f61a0b2)
- Time interval attribute now renders as `DecimalField` (45e774f)
- Notify: Add better error handling for "step edit"-popup (df76c12, 2366ff1)
- Better variation error handling (a877781)
- Fix issue where visibility errors caused an error (acda42f)
- Update admin category view (a404fa0)
- Admin datetimepicker (f1681e5)

Core
~~~~

- Rework `SimplePricing` and pricing in general (eaf40f3, 5cbeb44)
- Add non-ASCII support for supplier name (2c56b7e)
- Fix checking of duplicate settings (685d393)
- Add new fields to shop core (d56dd24)
- Add `DiscountPricingModule` (SHOOP-1289) (f9f3789)
- Fix PriceInfo usage with non-one quantities (SHOOP-1462) (1bb1c02)
- Fix shoop.core.migrations.0006 (b605d04)
- Tax clean-up and refactoring (SHOOP-975) (2cb5a50, 182daff)
- Prevent `Shop` being deleted when image was deleted (c0edb08)

Front
~~~~~

- An all-new dynamic theming system, Xtheme (49dfedb, a3d1c6d, 5930a96, d9b3b15,
  ab46bb5, 4f5c3fc, 5ca3dad, c40c620, db86c9a, f430bd0, 8e3791f, d99c221, 03f2976)
- Classic Gray: A new slick theme built on the Xtheme system (44 merges, not listed here)
- Add ordering for cross sells template helper (48a5f41)
- Fix `get_root_categories` performance (6d337fa)
- Maintenance mode (SHOOP-1153) (273ed37, eb7dbdb, 609d397, 5e72de0, b2d2952)
- template_helpers: Fix get_pagination_variables (a3770ea)
- Ensure user is logged in after activating account (fb22268)
- Customer URL now requires login (caf357c, bbcbbbf)
- Add support for Complex variations  (f61dadc)
- Add Default ErrorHandling (46152cd, 48ce0cc)
- Fix issue with variation children being listed for admin user (a4833dd)
- Front: Fix issue with variation children visible in search results (fc53234)

General/miscellaneous
~~~~~~~~~~~~~~~~~~~~~

- Run ESLint on all the things! (fa1c0e8)
- Prunes, manifests (63b3969)
- PEP8ify (5b575c4)
- Various fixes (09e5c9f)
- Tests: Make test_user_detail_contact_seed not fail randomly (53de20a)
- Miscellaneous tiny fixes (faafb26)
- Fixes (f02c10f)
- Cms duplicate (91f1567)
- Embetter patterns (4427755)
- Saner sanity tools (3b4d003)
- Workbench: Allow overriding couple settings from env (361c3d2)


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
