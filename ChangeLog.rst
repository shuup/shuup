Shoop Change Log
================

Unreleased
----------

- List all changes after 1.0.0 here (newer on top).  Each change on a
  separate bullet point line.  Wrap the file at 79 columns or so.  When
  releasing next version, the "Unreleased" header will be replaced with
  appropriate version header and this help text will be removed.

Version 1.1.0
-------------

Released on 2015-07-03 12:30 +0300.

- Improve "Getting Started with Shoop Development" documentation

- Add a basic REST API for reading/writing products and reading orders

- Use the database to store shopping baskets by default

- Implement pluggable shopping basket storage backends

- Implement basic contact group admin

- Add telemetry (usage statistics) system

- Add Dockerfile

- Improve admin login flow

- Document settings; make documentation builds available on ReadTheDocs

- Make release packaging much more robust

- Generate order keys in a secure manner

- Trim admin search strings

- Embetter admin order layouts

- Create the Shop as active with ``shoop_init`` management command

- Fix usages of ``Category.get_ancestors()`` in templates

- Remove Stripe integration (shoop.stripe)

  - It now lives in https://github.com/shoopio/shoop-stripe

- Core: Declare correct ``required_installed_apps`` in AppConfig

- Fix handling of tuple-format ``required_installed_apps``

- Fix Money class to not read settings at instance creation

- Fix management command ``shoop_show_settings`` for Python 3

- Add Addon documentation (doc/addons.rst)


Version 1.0.0
-------------

Released on 2015-06-04 16:30 +0300.

- The first Open Source version of Shoop.
