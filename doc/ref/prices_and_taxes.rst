Prices and Taxes in Shuup
=========================

This document gives an overview of Shuup's pricing and tax mechanics.
For deeper view about the implementation -- for example, if you're
implementing a price/tax related addon -- also read the
:doc:`../howto/prices_and_taxes_implementation` document.

.. _price-unit:

Price Unit
----------

Prices in Shuup have an unit that is combination of a currency and an
includes/excludes taxes flag.  That is, prices may be specified pretax
or with taxes included.  Which taxation type and currency is used is
usually decided by the `~shuup.core.models.Shop`, which has `currency`
and `prices_include_tax` fields.  In general, it is also possible that
the active `~shuup.core.pricing.PricingModule` uses a different price
unit that is specified by the shop.  Currently there is no such pricing
module in the Shuup Base distribution.

Different price units cannot be mixed: Adding a pretax price and a price
including taxes together would be an error, as would be adding USDs to
EURs.

The price unit of a `~shuup.core.models.Shop` can be changed as long as
there are no `Orders <shuup.core.models.Order>` created for the shop.

The price unit of an `~shuup.core.models.Order` is stored in its
``currency`` and ``prices_include_tax`` fields.  The line prices of an
order are stored in that unit, but the total price of order is stored
with and without taxes in the ``taxful_price`` and ``taxless_price``
fields.

Calculation of Taxes
--------------------

How Taxes Are Determined
~~~~~~~~~~~~~~~~~~~~~~~~

Taxes in Shuup are implemented by a `tax module
<shuup.core.taxing.TaxModule>`.  The Shuup Base distribution ships a tax
module called :ref:`Default Tax <default-tax-module>`, but it is
possible to plug in another tax module via :doc:`../howto/addons` or to
implement a new one.

The responsibilities of a tax module are to calculate taxes for an order
or for separate items (e.g. product, shipping or some other taxable
item).  The most important function of a tax module is to take an order
source (such as a basket), which has lines (with pre-tax prices or
prices with tax included) and fill in the taxes for each line in the
source.

When Taxes Are Determined
~~~~~~~~~~~~~~~~~~~~~~~~~

There are two modes of operation for calculating the taxes: on-demand
and on-checkout.  If current tax module declares that tax calculation is
"cheap" (does not cost a transaction fee and is fast to compute) and
`~shuup.core.settings.SHUUP_CALCULATE_TAXES_AUTOMATICALLY_IF_POSSIBLE`
setting is true, then on-demand calculation will be used.  Otherwise
on-checkout calculation will be used.

With on-checkout tax calculation mode Shuup calculates taxes for a
basket in the confirmation phase of the checkout process or in the
confirmation phase of the order creating UI in the Shop Admin.  This
means that taxes are not known for items in the basket, product listings
or on the detail page of a product.  The reason for not calculating
taxes before the confirm phase is that the active tax module might query
tax information from an external source which might be prohibitively
slow or cost a transaction fee.

With on-demand tax calculation mode calculation happens when showing
prices in the shop, if prices returned by the current pricing module are
pretax and current price display options demand prices including taxes
or the other way around.

Taxes in Orders
---------------

Taxes are stored in order lines.  Each order line can have several taxes
applied and each of them is stored to a separate `line tax
<shuup.core.models.OrderLineTax>` object linked to the order line.
These line tax objects contain references to `~shuup.core.models.Tax`
objects, the name of the tax, the applied amount and the base amount the
tax is calculated off of.

.. _default-tax-module:

The Default Tax Module
----------------------

Shuup Default Tax is a tax module that calculates taxes based on a set
of static rules stored in the database.  A tax rule applies a tax for an
order line or any other taxable item (e.g. product or shipping method).
An item can be taxed with several taxes, which will be either added
together or compounded over each other.

.. _defining-default-tax-rules:

Defining Tax Rules for The Default Tax Module
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The tax rules of Default Tax can be managed in the Shuup Shop Admin
(*Menu* → *Taxes* → *Tax Rules*).

Most fields of the tax rule determine the conditions when the rule
applies.  All non-empty fields must match for the rule to apply.  Empty
fields are not considered, e.g. if the "Customer tax groups" field is
left empty, all customer tax groups will match.  You may use these
conditions to apply tax rules e.g. only for a specific country or area.

Area specific matching criteria fields are specified with a pattern that
is able to match multiple values.  See the help text in the admin view
for details on how to write those patterns.

If all conditions of a tax rule match, the rule will be applied.  That
means that the tax specified in the rule will be added for the item.  If
there are several rules to be applied for an item, the total tax is
determined by the priority field.  Rules with same priorities are
calculated as added (which would be the case for taxes in the United
States) while rules with different priorities define compounding taxes
(for example the PST taxes in Canada's Quebec province).

Tax rules may also define override group numbers.  If several rules
match, only the rules with the highest override group number will be
effective.  This can be used, for example, to implement tax exemption by
adding a rule with very high override group number that sets a zero tax.
