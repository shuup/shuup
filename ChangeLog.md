Shoop Change Log
================

## Unreleased

- List all changes after 1.0.0 here (newer on top).  Each change on a
  separate bullet point line.  Wrap the file at 79 columns or so.  When
  releasing next version, the "Unreleased" header will be replaced with
  appropriate version header and this help text will be removed.

- Create the Shop as active with `shoop_init` management command
- Fix usages of `Category.get_ancestors()` in templates
- Remove Stripe integration (shoop.stripe)
  - It now lives in https://github.com/shoopio/shoop-stripe
- Core: Declare correct `required_installed_apps` in AppConfig
- Fix handling of tuple-format `required_installed_apps`
- Fix Money class to not read settings at instance creation
- Fix management command `shoop_show_settings` for Python 3
- Add Addon documentation (doc/addons.rst)

## Version 1.0.0, released 2015-06-04 16:30 +0300

- The first Open Source version of Shoop.
