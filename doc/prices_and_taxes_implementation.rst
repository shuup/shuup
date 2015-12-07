Implementation of Prices and Taxes in Shoop
===========================================

This document describes deeper details about price and tax
implementation in Shoop from a developer's point of view.  To understand
the basics, please read :doc:`prices_and_taxes` first.

.. _price-tax-types:

Types Used for Prices and Taxes
-------------------------------

`~shoop.utils.money.Money`

  Used to represent money amounts (that are not prices).  It is
  basically a `~decimal.Decimal` number with a currency.

`~shoop.core.pricing.Price`

  Used to represent prices. `Price` is a `~shoop.utils.money.Money` with
  an `includes_tax` property.  It has has two subclasses:
  `~shoop.core.pricing.TaxfulPrice` and
  `~shoop.core.pricing.TaxlessPrice`.

  There should usually be no need to create prices directly with these
  classes; see :ref:`creating-prices`.

`~shoop.core.pricing.Priceful`

  An interface for accessing the price information of a product, order
  line, basket line, or whatever.  See :ref:`accessing-prices`.

`~shoop.core.pricing.PriceInfo`

  A class for describing an item's price information.

`~shoop.core.pricing.PricingModule`

  An interface for querying prices of products.

`~shoop.core.pricing.PricingContext`

  A container for variables that affect pricing.  Pricing modules may
  subclass this.

`~shoop.core.pricing.PricingContextable`

  An interface for objects that can be converted to a pricing context.
  Instances of `PricingContext` or `~django.http.HttpRequest` satisfy
  this interface.

`~shoop.core.taxing.LineTax`

  An interface for describing a calculated tax of a line in order or
  basket.  Has a reference to the line and to the applied tax and the
  calculated amount of tax. One line could have several taxes applied,
  each is presented with a separate `LineTax`.

`~shoop.core.taxing.SourceLineTax`

  A container for a calculated tax of a
  `~shoop.core.order_creator.SourceLine` (or
  `~shoop.front.basket.objects.BasketLine`).  Implements the `LineTax`
  interface.

`~shoop.core.models.OrderLineTax`

  A Django model for persistently storing the calculated tax of an
  `~shoop.core.models.OrderLine`.  Implements the `LineTax` interface.

`~shoop.core.models.Tax`

  A Django model for a tax with name, code, and percentage rate or fixed
  amount.  Fixed amounts are not yet supported.

  .. TODO:: Fix this when fixed amounts are supported.

`~shoop.core.taxing.TaxableItem`

  An interface for items that can be taxed.  Implemented by
  `~shoop.core.models.Product`, `~shoop.core.models.ShippingMethod`,
  `~shoop.core.models.PaymentMethod` and
  `~shoop.core.order_creator.SourceLine`.

`~shoop.core.models.TaxClass`

  A Django model for a tax class.  Taxable items (e.g. products, methods
  or lines) are grouped to tax classes to make it possible to have
  different taxation rules for different groups of items.

`~shoop.core.models.CustomerTaxGroup`

  A Django model for grouping customers to make it possible to have
  different taxation rules for different groups of customers.  Shoop
  assigns separate `CustomerTaxGroup`s for a
  `~shoop.core.models.PersonContact` and a
  `~shoop.core.models.CompanyContact` by default.

`~shoop.core.taxing.TaxModule`

  An interface for calculating the taxes of an
  `~shoop.core.order_creator.OrderSource` or any `TaxableItem`.  The
  Shoop Base distribution ships a concrete implementation of a
  `TaxModule` called `~shoop.default_tax.module.DefaultTaxModule`.  It
  is a based on a table of tax rules (saved with
  `~shoop.default_tax.models.TaxRule` model).  See
  :ref:`default-tax-module`.  Used `TaxModule` can be changed with
  `~shoop.core.settings.SHOOP_TAX_MODULE` setting.

`~shoop.core.taxing.TaxedPrice`

  A type to represent the return value of tax calculation.  Contains a
  pair of prices, `TaxfulPrice` and `TaxlessPrice`, of which one is the
  original price before the calculation and the other is the calculated
  price. Also contains a list of the applied taxes.  `TaxedPrice` is the
  return type of `~shoop.core.taxing.TaxModule.get_taxed_price_for`
  method in the `TaxModule` interface.

`~shoop.core.taxing.TaxingContext`

  A container for variables that affect taxing, such as customer tax
  group, customer tax number, location (country, postal code, etc.).
  Used in the `TaxModule` interface. Note: This is *not* usually
  subclassed.

.. _creating-prices:

Creating Prices
---------------

When implementing a `~shoop.core.pricing.PricingModule` or another
module that has to create prices, use the `Shop.create_price
<shoop.core.models.Shop.create_price>` method.  It makes sure that all
prices have the same :ref:`price unit <price-unit>`.

.. _accessing-prices:

Accessing Prices of Product or Line
-----------------------------------

There is a `~shoop.core.pricing.Priceful` interface for accessing
prices.  It is implemented by `~shoop.core.models.OrderLine` and
`~shoop.core.order_creator.SourceLine`,
`~shoop.front.basket.objects.BasketLine`, and
`~shoop.core.pricing.PriceInfo` which is returned e.g. by
`~shoop.core.models.Product.get_price_info` method.
