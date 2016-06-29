Shoop 3.0.0 Release Notes
=========================

Released on 2016-01-21 11:15 +0200.

Here's a few highlights of new features, improvements and fixes in Shoop
3.0.0 since 2.0.0.  For complete list of changes see
:doc:`../shoop-changelog` or `Git commit log
<https://github.com/shuup/shoop/commits/v3.0.0>`__.

There's also update instructions for :ref:`updating from 2.0
<updating-from-2-to-3>`.

New Features
------------

* Creating orders from the Admin

* Localization

  - Provide tools for collecting and compiling translated messages.
  - Add language chooser to Classic Gray theme.
  - Implement JavaScript translations.
  - Xtheme plugins are now translatable.
  - More messages have been marked for translation.
  - Included translations: English, Finnish, Chinese and Japanese.

Improvements
------------

* Allow addons to inject resources to Xtheme templates

* Enable email login and password recovery with username

* Show product media at order history and product detail pages

* Show Shoop version number in Admin

* Xtheme editor improvements

* Tax system improvements

  - Document the tax system (see :doc:`../prices_and_taxes`)
  - Implement override groups for Default Tax
  - Clean-up internal tax/price related APIs

* And many more

Fixes
-----

* Xtheme: Don't crash when trying to revert unsaved configuration

* Default Tax: Fix calculation of added and compounded taxes

* And many more

Miscellaneous
-------------

* Test are now ran also on `Travis <https://travis-ci.org/shuup>`__

* Python package dependencies are updated and not so strict anymore

* Node package dependencies are locked down with npm-shrinkwrap

.. _updating-from-2-to-3:

Updating from 2.0
-----------------

Shoop 3.0 introduces some API changes which could affect projects or
addons based on Shoop 2.0.  Here is a list of the API changes and
instructions how to update your code.

* `Priceful.total_price` has been removed.  This affects
  e.g. `OrderLine`, `BasketLine` and `PriceInfo` objects.

  - Use `Priceful.price` instead.

* `PriceTaxContext` is removed.

  - You should not need it.  Use `PricingContext` or `TaxingContext`
    where appropriate.

* Default Theme is removed.

  - It is available as a separate package from
    https://github.com/shuup/shuup-simple-theme

* `Address` is split to `MutableAddress` and `ImmutableAddress`.
  `Address` is converted to abstract base class.

  - Database changes should be handled by migrations.
  - Usually usages of `Address` should be converted to `MutableAddress`,
    but they should be converted to immutable with
    `Address.to_immutable` for e.g. `Order` addresses.

* Submodules of `shoop.core.pricing` are now private.

  - Use the API exposed by the `shoop.core.pricing` module's
    ``__init__.py``.  E.g. use `shoop.core.pricing.PriceInfo` instead of
    `shoop.core.pricing.price_info.PriceInfo`.

* Submodules of `shoop.core.order_creator` are now private.

  - Use the API exposed by the module's ``__init__.py``.

* `shoop.core.utils.reference` is removed.

* Some submodules of `shoop.xtheme` are now private.

  - Use symbols directly from `shoop.xtheme`, e.g. `shoop.xtheme.Theme`
    instead of `shoop.xtheme.theme.Theme` or
    `shoop.xtheme.TemplatedPlugin` instead of
    `shoop.xtheme.plugins.TemplatedPlugin`.

* Submodules of `shoop.core.models` are now private.

  - Use the models or enums directly from the main package.

* `shoop.core.models.product_variation` is removed.

  - Relevant functions are now available as `Product` methods.
