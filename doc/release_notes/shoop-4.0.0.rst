Shoop 4.0.0 Release Notes
=========================

Released on 2016-06-29 21:30 +0300.

This release includes many new features, bug fixes and improvements in
over 400 non-merge commits since 3.0.0.  Highlights of the changes are
listed here, but for complete list of changes see
:doc:`../shoop-changelog` or `Git commit log
<https://github.com/shuup/shoop/commits/v4.0.0>`__.

This is also the last release of Shoop, since the product name will
change to Shuup.  The same code base with "shoop" replaced by "shuup"
will be released as Shuup 0.4 shortly after Shoop 4.0 release.

There's also update instructions for :ref:`updating from 3.0
<updating-from-3-to-4>`.

New Features
------------

* Campaigns

  - Campaigns and coupons can now be managed in Admin

* Order printouts

  - Allows creating PDF printouts of orders from Admin
  - Requires WeasyPrint to be installed (available via pip)

* Stock management

  - Stock counts can now be managed with Simple Supplier module

* Payments and refunds

  - Payments and refunds for orders may now be created in Admin

* Order editing

  - Non-delivered orders without payments may now be edited in Admin

* Package products

  - Package products can now be created in Admin

* Shipping and payment behavior components

  - Shipping and payment methods management is reformed to allow
    versatile extension with addons.  One of the changes introduces a
    new concept called service behavior components.  These components
    allow merchants to customize behavior of the payment and shipping
    methods in more detail than before.

* Price display options

  - It is now possible to define how prices are rendered for a customer
    by a contact group setting.  Choices are: show prices including
    taxes, excluding taxes or hide prices.

* Guide

  - Guide app integrates search results from Shoop Guide documentation
    into Admin search

Miscellaneous
-------------

* Brazilian Portuguese translations (pt_BR)

  - Thanks to Christian and Jonathan Hess

* Initialize checkout addresses from customer data

  - Thanks to Jason Sujjon

.. _updating-from-3-to-4:

Updating from 3.0
-----------------

Shoop 4.0 introduces many API changes which could affect projects or
addons based on Shoop 3.0.  Here is a list of the API changes and
instructions how to update your code.

* Database changes

  Database migration from 3.0.0 should go smoothly with MySQL and SQLite
  databases.  Unfortunately we don't test with PostgreSQL currently and
  found out just before the release that our migrations don't work for
  PostgreSQL.  Setting ``connection.features.can_rollback_ddl`` to
  ``False`` (e.g. in your ``manage.py``) may help in that case.

* Payment and shipping service API is refactored

  - This affects payment and shipping method addons.
  - See :doc:`../services` document for introduction to the new API.
  - See this `pull request
    <https://github.com/shuup/shuup-checkoutfi/pull/1/files>`__ as an
    example how to refactor the addon code.

* Simple Pricing is renamed to Customer Group Pricing.

  - Prices have to be migrated manually.

* Enum value ``OrderLineType.CAMPAIGN`` is renamed to ``DISCOUNT``

  - Replace usages of ``CAMPAIGN`` line types with ``DISCOUNT``

* Discount Pricing is removed.

  - Use the new Campaigns features instead.

* ``order_creator_finished`` signal is moved from Front to Core

  - Update your imports.
