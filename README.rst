Shoop
=====

Shoop is an Open Source E-Commerce Platform based on Django and Python.

https://shoop.io/

Copyright
---------

Copyright (C) 2012-2016 by Shoop Ltd. <contact@shoop.io>

Shoop is International Registered Trademark & Property of Shoop Ltd.,
Business ID: FI24815722, Business Address: Aurakatu 12 B, 20100 Turku,
Finland.

CLA
---

Contributor License Agreement is required for any contribution to this
project.  Agreement is signed as a part of pull request process.  See
the CLA.rst file distributed with Shoop.

License
-------

Shoop is published under the GNU Affero General Public License,
version 3 (AGPLv3). See the LICENSE file distributed with Shoop.

Some external libraries and contributions bundled with Shoop may be
published under other AGPLv3-compatible licenses.  For these, please
refer to VENDOR-LICENSES.md file in the source code tree or the licenses
included within each package.

Chat
----

We have a Gitter chat room for Shoop.  Come chat with us!  |Join chat|

.. |Join chat| image:: https://badges.gitter.im/Join%20Chat.svg
   :target: https://gitter.im/shoopio/shoop

Getting started with Shoop development
--------------------------------------

See `Getting Started with Shoop Development
<http://shoop.readthedocs.org/en/latest/getting_started_dev.html>`__.

Documentation
-------------

Shoop documentation is available online at `Read the Docs
<http://shoop.readthedocs.org/>`__.

Documentation is built with `Sphinx <http://sphinx-doc.org/>`__.

Issue the following commands to build the documentation:

.. code:: sh

    pip install Sphinx  # to install Sphinx
    cd doc && make html

To update the API documentation rst files, e.g. after adding new
modules, use command:

.. code:: sh

    ./generate_apidoc.py
