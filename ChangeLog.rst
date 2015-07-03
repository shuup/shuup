Shoop Change Log
================

Unreleased
----------

- List all changes after 1.0.0 here (newer on top).  Each change on a
  separate bullet point line.  Wrap the file at 79 columns or so.  When
  releasing next version, the "Unreleased" header will be replaced with
  appropriate version header and this help text will be removed.

- Add a basic REST API for reading/writing products and reading orders
  (merge 7a31a88)
- Use the database to store shopping baskets by default (merge 458d6ef)
- Implement pluggable shopping basket storage backends (merge 458d6ef)
- Implement basic contact group admin (merge 185bf1c)
- Add telemetry (usage statistics) system (merge c42e243)
- Add Dockerfile (merge 737666d)
- Improve admin login flow (merge 8bb9e05)
- Document settings; make documentation builds available on ReadTheDocs
  (merge 92e7959)
- Make release packaging much more robust (merge e1c2cda)
- Generate order keys in a secure manner (e3861a0)
- Trim admin search strings (09ba9cd)
- Embetter admin order layouts (673da85)
- Create the Shop as active with ``shoop_init`` management command
  (1d99aa4)
- Fix usages of ``Category.get_ancestors()`` in templates (5bdf8a1)
- Remove Stripe integration (shoop.stripe) (fe87fab)
  -  It now lives in https://github.com/shoopio/shoop-stripe
- Core: Declare correct ``required_installed_apps`` in AppConfig
  (a66b4e4)
- Fix handling of tuple-format ``required_installed_apps``
- Fix Money class to not read settings at instance creation (1e8987d)
- Fix management command ``shoop_show_settings`` for Python 3 (6112472)
- Add Addon documentation (doc/addons.rst)

Version 1.0.0, released 2015-06-04 16:30 +0300
----------------------------------------------

- The first Open Source version of Shoop.
