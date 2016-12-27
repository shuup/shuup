Implementation of Prices and Taxes in Shuup
===========================================

This document describes deeper details about price and tax
implementation in Shuup from a developer's point of view.  To understand
the basics, please read :doc:`../ref/prices_and_taxes` first.

.. _price-tax-types:

Types Used for Prices and Taxes
-------------------------------

`~shuup.utils.money.Money`

  Used to represent money amounts (that are not prices).  It is
  basically a `~decimal.Decimal` number with a currency.

`~shuup.core.pricing.Price`

  Used to represent prices. `Price` is a `~shuup.utils.money.Money` with
  an `includes_tax` property.  It has has two subclasses:
  `~shuup.core.pricing.TaxfulPrice` and
  `~shuup.core.pricing.TaxlessPrice`.

  There should usually be no need to create prices directly with these
  classes; see :ref:`creating-prices`.

`~shuup.core.pricing.Priceful`

  An interface for accessing the price information of a product, order
  line, basket line, or whatever.  See :ref:`accessing-prices`.

`~shuup.core.pricing.PriceInfo`

  A class for describing an item's price information.

`~shuup.core.pricing.PricingModule`

  An interface for querying prices of products.

`~shuup.core.pricing.PricingContext`

  A container for variables that affect pricing.  Pricing modules may
  subclass this.

`~shuup.core.pricing.PricingContextable`

  An interface for objects that can be converted to a pricing context.
  Instances of `PricingContext` or `~django.http.HttpRequest` satisfy
  this interface.

`~shuup.core.taxing.LineTax`

  An interface for describing a calculated tax of a line in order or
  basket.  Has a reference to the line and to the applied tax and the
  calculated amount of tax. One line could have several taxes applied,
  each is presented with a separate `LineTax`.

`~shuup.core.taxing.SourceLineTax`

  A container for a calculated tax of a
  `~shuup.core.order_creator.SourceLine` (or
  `~shuup.front.basket.objects.BasketLine`).  Implements the `LineTax`
  interface.

`~shuup.core.models.OrderLineTax`

  A Django model for persistently storing the calculated tax of an
  `~shuup.core.models.OrderLine`.  Implements the `LineTax` interface.

`~shuup.core.models.Tax`

  A Django model for a tax with name, code, and percentage rate or fixed
  amount.  Fixed amounts are not yet supported.

  .. TODO:: Fix this when fixed amounts are supported.

`~shuup.core.taxing.TaxableItem`

  An interface for items that can be taxed.  Implemented by
  `~shuup.core.models.Product`, `~shuup.core.models.ShippingMethod`,
  `~shuup.core.models.PaymentMethod` and
  `~shuup.core.order_creator.SourceLine`.

`~shuup.core.models.TaxClass`

  A Django model for a tax class.  Taxable items (e.g. products, methods
  or lines) are grouped to tax classes to make it possible to have
  different taxation rules for different groups of items.

`~shuup.core.models.CustomerTaxGroup`

  A Django model for grouping customers to make it possible to have
  different taxation rules for different groups of customers.  Shuup
  assigns separate `CustomerTaxGroup`s for a
  `~shuup.core.models.PersonContact` and a
  `~shuup.core.models.CompanyContact` by default.

`~shuup.core.taxing.TaxModule`

  An interface for calculating the taxes of an
  `~shuup.core.order_creator.OrderSource` or any `TaxableItem`.  The
  Shuup Base distribution ships a concrete implementation of a
  `TaxModule` called `~shuup.default_tax.module.DefaultTaxModule`.  It
  is a based on a table of tax rules (saved with
  `~shuup.default_tax.models.TaxRule` model).  See
  :ref:`default-tax-module`.  Used `TaxModule` can be changed with
  `~shuup.core.settings.SHUUP_TAX_MODULE` setting.

`~shuup.core.taxing.TaxedPrice`

  A type to represent the return value of tax calculation.  Contains a
  pair of prices, `TaxfulPrice` and `TaxlessPrice`, of which one is the
  original price before the calculation and the other is the calculated
  price. Also contains a list of the applied taxes.  `TaxedPrice` is the
  return type of `~shuup.core.taxing.TaxModule.get_taxed_price_for`
  method in the `TaxModule` interface.

`~shuup.core.taxing.TaxingContext`

  A container for variables that affect taxing, such as customer tax
  group, customer tax number, location (country, postal code, etc.).
  Used in the `TaxModule` interface. Note: This is *not* usually
  subclassed.

.. _creating-prices:

Creating Prices
---------------

When implementing a `~shuup.core.pricing.PricingModule` or another
module that has to create prices, use the `Shop.create_price
<shuup.core.models.Shop.create_price>` method.  It makes sure that all
prices have the same :ref:`price unit <price-unit>`.

.. _accessing-prices:

Accessing Prices of Product or Line
-----------------------------------

There is a `~shuup.core.pricing.Priceful` interface for accessing
prices.  It is implemented by `~shuup.core.models.OrderLine` and
`~shuup.core.order_creator.SourceLine`,
`~shuup.front.basket.objects.BasketLine`, and
`~shuup.core.pricing.PriceInfo` which is returned e.g. by
`~shuup.core.models.Product.get_price_info` method.
