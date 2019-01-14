.. image:: https://travis-ci.org/shuup/shuup.svg?branch=master
    :target: https://travis-ci.org/shuup/shuup
.. image:: https://coveralls.io/repos/github/shuup/shuup/badge.svg?branch=master
   :target: https://coveralls.io/github/shuup/shuup?branch=master
.. image:: https://img.shields.io/pypi/v/shuup.svg
   :alt: PyPI
   :target: https://github.com/shuup/shuup

Shuup
=====

Shuup is an Open Source E-Commerce Platform based on Django and Python.

https://shuup.com/

Copyright
---------

Copyright (C) 2012-2019 by Shoop Commerce Ltd. <support@shuup.com>

Shuup is International Registered Trademark & Property of Shoop Commerce Ltd.,
Business ID: FI27184225,
Business Address: Iso-Roobertinkatu 20-22, 00120 HELSINKI, Finland.

CLA
---

Contributor License Agreement is required for any contribution to this
project.  Agreement is signed as a part of pull request process.  See
the CLA.rst file distributed with Shuup.

License
-------

Shuup is published under Open Software License version 3.0 (OSL-3.0).
See the LICENSE file distributed with Shuup.

Some external libraries and contributions bundled with Shuup may be
published under other compatible licenses. For these, please
refer to VENDOR-LICENSES.md file in the source code tree or the licenses
included within each package.

Chat
----

We have a Gitter chat room for Shuup.  Come chat with us!  |Join chat|

.. |Join chat| image:: https://badges.gitter.im/Join%20Chat.svg
   :target: https://gitter.im/shuup/shuup

Install Shuup
-------------

See `Getting Started
<http://shuup.readthedocs.io/en/latest/howto/getting_started.html>`__.

For simple project example see our `Django-project template <https://github.com/shuup/shuup-project-template>`__.

Getting Started with Shuup development
--------------------------------------

See `Getting Started with Shuup Development
<http://shuup.readthedocs.io/en/latest/howto/getting_started_dev.html>`__.

Contributing to Shuup
---------------------

Interested in contributing to Shuup? Please see our `Contribution Guide
<https://www.shuup.com/contributions/>`__.

Documentation
-------------

Shuup documentation is available online at `Read the Docs
<http://shuup.readthedocs.org/>`__.

Documentation is built with `Sphinx <http://sphinx-doc.org/>`__.

Issue the following commands to build the documentation:

.. code:: sh

    pip install -r requirements-doc.txt
    cd doc && make html

To update the API documentation rst files, e.g. after adding new
modules, use command:

.. code:: sh

    ./generate_apidoc.py

Roadmap
-------

* Per object placeholders. Option to add content per contact group, category, product and CMS page. `#1220 <https://github.com/shuup/shuup/issues/1220>`__ :white_check_mark:.
* Pricing cache. To improve the performance issues with complex catalog campaigns. `#1163 <https://github.com/shuup/shuup/issues/1163>`__ :white_check_mark:.
* Improve shop product purchasable attribute. `#1281 <https://github.com/shuup/shuup/issues/1281>`__ :white_check_mark:.
* Option for 'centrally' or 'separately' managed products. `#1275 <https://github.com/shuup/shuup/issues/1275>`__.
* Improve product stock behavior. `#1249 <https://github.com/shuup/shuup/issues/1249>`__.
* Improved unit tests for the multishop feature. `#1160 <https://github.com/shuup/shuup/issues/1160>`__.
* Improve order status and order status history. `#1211 <https://github.com/shuup/shuup/issues/1211>`__.
* Initial support for Django 2.0. `#1289 <https://github.com/shuup/shuup/issues/1289>`__.
* OS Admin design/UX overhaul.
* Various smaller issues from the issues-list.

OS Addons
---------

* `Django-project template <https://github.com/shuup/shuup-project-template>`__. Django-project template.

* `Shuup Product Reviews <https://github.com/shuup/shuup-product-reviews>`__. Shuup Product Reviews.
* `Shuup Stripe <https://github.com/shuup/shuup-stripe>`__. Stripe Payment Processor Addon for Shuup.
* `Shuup Wishlist <https://github.com/shuup/shuup-wishlist>`__. Shuup Wishlist Addon.
* `Shuup Checkoutfi <https://github.com/shuup/shuup-checkoutfi>`__. Checkout.fi integration for Shuup.
* `Shuup Yaml <https://github.com/shuup/shuup-yaml>`__. Import categories, manufacturers and products to Shuup.
* `Shuup Mailchimp <https://github.com/shuup/shuup-mailchimp>`__. Mailchimp integration for Shuup (New v0.7.8 released).
* `Shuup Xtheme Layouts <https://github.com/shuup/shuup-xtheme-extra-layouts>`__. Xtheme layouts for Shuup.
* `Shuup Category Organizer <https://github.com/shuup/shuup-category-organizer>`__. Shuup Category Organizer.

The purpose of these addons, is to demonstrate how to build
other simple addons to extend Shuup. To learn more, here are
some useful links about how to extend Shuup.

* `Provides system <https://shuup.readthedocs.io/en/latest/ref/provides.html>`__.
* `Core settings <https://shuup.readthedocs.io/en/latest/api/shuup.core.html#module-shuup.core.settings>`__.
* `Front settings <https://shuup.readthedocs.io/en/latest/api/shuup.front.html#module-shuup.front.settings>`__.
* `Admin settings <https://shuup.readthedocs.io/en/latest/api/shuup.admin.html#module-shuup.admin.settings>`__.
* `Extending Shuup <https://shuup.readthedocs.io/en/latest/#extending-shuup>`__.


Admin Preview
-------------

.. image:: doc/_static/admin_shop_product.png
    :target: doc/_static/admin_shop_product.png
    :height: 300px

.. image:: doc/_static/admin_order_detail.png
    :target: doc/_static/admin_order_detail.png
    :height: 300px
