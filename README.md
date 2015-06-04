# Shoop

Shoop is an Open Source E-Commerce Platform based on Django and Python.

## Copyright

Copyright (C) 2012-2015 by Shoop Ltd. <contact@shoop.io>

Shoop is International Registered Trademark & Property of Shoop Ltd.,
Business ID: FI24815722, Business Address: Aurakatu 12 B, 20100 Turku,
Finland.

## License

Shoop is published under the GNU Affero General Public License,
version 3 (AGPLv3). See the LICENSE file distributed with Shoop.

Some external libraries and contributions bundled with Shoop may be
published under other AGPLv3-compatible licenses.  For these, please
refer to VENDOR-LICENSES.md file in the source code tree or the licenses
included within each package.

## Getting started with Shoop development

See [Getting Started](doc/getting_started_dev.rst).

## Documentation

Documentation is built with [Sphinx](http://sphinx-doc.org/).

Issue the following commands to build the documentation:

```sh
pip install Sphinx  # to install Sphinx
cd doc && make html
```

To update the API documentation rst files, e.g. after adding new
modules, use command:

```sh
./generate_apidoc.py
```
