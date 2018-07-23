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

Copyright (C) 2012-2018 by Shuup Inc. <support@shuup.com>

Shuup is International Registered Trademark & Property of Shuup Inc.,
Business Address: 1013 Centre Road, Suite 403-B,
Wilmington, Delaware 19805,
United States Of America

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
* Pricing cache. To improve the performance issues with complex catalog campaigns. `#1163 <https://github.com/shuup/shuup/issues/1163>`__.
* Option for 'centrally' or 'separately' managed products. `#1275 <https://github.com/shuup/shuup/issues/1275>`__.
* Improve shop product purchasable attribute. `#1281 <https://github.com/shuup/shuup/issues/1281>`__.
* Improve product stock behavior. `#1249 <https://github.com/shuup/shuup/issues/1249>`__.
* Improved unit tests for the multishop feature. `#1160 <https://github.com/shuup/shuup/issues/1160>`__.
* Initial support for Django 2.0. `#1289 <https://github.com/shuup/shuup/issues/1289>`__.
* OS Admin design/UX overhaul.
* Various smaller issues from the issues-list.
