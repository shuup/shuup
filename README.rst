.. image:: https://travis-ci.org/shuup/shuup.svg?branch=master
    :target: https://travis-ci.org/shuup/shuup
.. image:: https://coveralls.io/repos/github/shuup/shuup/badge.svg?branch=master
   :target: https://coveralls.io/github/shuup/shuup?branch=master

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
