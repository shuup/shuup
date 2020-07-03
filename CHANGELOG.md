# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

List all changes after the last release here (newer on top). Each change on a separate bullet point line.

### Changed

- Add theme for the shop in `shuup_init`
- Make the shop not be in maintenance mode in `shuup_init`

## [1.11.2] - 2020-07-03

- Move workbench sqlite database location for upcoming Docker setup

## [1.11.1] - 2020-07-03

### Added

- Admin: Add settings for controlling allowing HTML in product and vendor descriptions


## [1.11.0] - 2020-07-02

### Changed

- Importer: add context object while initializing a importer class
- Core: use UUID in basket IDs to prevent possible duplicates
- Core: save basket shipping and billing address as dictionary when id is not available
- Front: remove the custom _load() implementation from the basket as it is the same as the core
- Core: ignore lines that are not from the given source while calculating taxes
- Campaigns: do not apply campaigns in baskets configured to a supplier
- Admin: change service admin to list only providers that the current user can access
- Use UUID4 while generating order line ids by default
- Admin: Improve message banners, by:
    - Resetting the timeout for hiding the messages when a new message is added.
    - Immediately clearing the already hidden messages a when new one is added.
    - Not hiding messages when clicking just random background elements.
    - Allowing dismissing all of the messages by clicking any one of them anywhere.

### Added

- Admin: add improved product copy
- Core: add task runner to support running tasks using 3rd party services like Celery
- Core: add shops and supplier to ServiceProvider and Service models
- Front: add feature for checkout phases to spawn extra phases
- Add custom get_ip method and use it everywhere
- Importer: add permissions for all the diffrent types of importers
- Importer: add context class to data importer

### Removed

- Travis jobs for Django 1.8 and 1.9

### Fixed

- Removed the kind prefix from feedback messages using Django messages to prevent duplicate strings.
- Fixed the way the permissions identifier are split in admin
- Fixed issue that was importing User model directly
- Core: changed `del` basket command handler to not try to parse the basket line into an integer


## [1.10.16] - 2020-06-03

- Simple CMS: Fix a bug with the page links plugin

## [1.10.15] - 2020-06-02

### Changed

- Front: Ensure company name and tax number is set to both billing and shipping address same way
as when filled through company form when customer is not logged in. Company name and tax number
at order addresses seems to help with some taxation logic as well as makes things more consistent.

### Fixed

- Admin: Make sure related custom columns are added accrodingly. Fix issue with filtering through columns
that are by default hidden

## [1.10.14] - 2020-05-27

### Fixed

- Front: only show carousel title when there is one

### Changed

- Notify: Add AccountActivation event. AccountActivation event is
  triggered only when the user is activated for the first time.
- Front: improve next parameter with registration. Check GET
  parameter first and then fallback to POST data.

## [1.10.13] - 2020-05-20

- Admin: fix width issue with picotable images
- Admin: fix bugs in order edit and improve it one step closer to
  multivendor world. Now supports situation when vendors does not
  share products.
     - Add option to make shipping and payment method optional
     - Add supplier to pricing context
     - Show supplier name on product column
     - Make auto add for product select false by default
     - Fix product select2 missing URL and data handler since
       the whole ajax method was passed as attrs.
     - Add option to open/close collapsed content sections in mobile
- Core: add option to enable order edit for multiple vendors
- Front: do not stack history on product list when filters are changed.
  Instead replace state so back-buttons works nicely.
- Front: prevent image Lightbox touching history so you do not need
  to click back 6 times after you have viewed all images.

## [1.10.12] - 2020-05-05

### Added

- Admin: add error message when upload fails. At media queue complete do not
  resave product media if the file-count has not changed. This for example
  prevents media save when the upload itself fails.
- Admin: add option to override dropzone upload path by using data attribute
- Admin: add upload path to browser URLs and use it to fallback on media
  uploads when the actual media path is not available.
- Admin: Ability to delete manufacturer
- Admin: Ability to login as the selected contact if it's a user

### Fixed

- Admin: Now when activating/deactivating user it's contact will also change
- Admin: New notification for when a account get's reactivated

## [1.10.11] - 2020-04-23

### Fixed

- Discounts: create different admin module for archived discounts to fix breadcrumbs
- Fix product pagination by not overriding the state with undefined values

### Fixed

- Middleware: fix so it trys to take the users timezone first, then the suppliers, last the projects TIME_ZONE

### Changed

- Front: customize sort options through settings

## [1.10.10] - 2020-03-24

### Fixed

- Admin: Notification name when deleteing it
- Admin: Update contact list so that it only shows customers by default
- Front: Fix typo

### Changed

- Front: Add supplier choice to best selling product context function
- Admin: allow sorting categories by name
- Admin: show product orderability errors as list


## [1.10.9] - 2020-03-24

### Fixed

- Admin: remove pinned /sa/ URL from scripts to support dynamic admin URLs
- Admin: Fix graphical (incorrect indent) bug in Product / Stock Management

## [1.10.8] - 2020-03-20

### Changed

- Admin: add spinner and progressbar options components through Bootstrap 4.

### Fixed

- Issue running category filter browser test with Travis


## [1.10.7] - 2020-03-09

### Fixed

- Admin: remove pinned /sa/ URL from scripts to support dynamic admin URLs
- Front: keep the current query string parameters as the initial state
  when refreshing product filters.

### Changed

- Admin: fix page jumps after reaload
- Admin: make browser urls support urls with parameters

## [1.10.6] - 2020-02-28

### Changed

- Core: supplier name max length to 128 from 64

## [1.10.5] - 2020-02-27

### Added

- Add option to send notification event at password recovery

### Changed

- Improve the admin modals to use flexbox and work better on small devices

### Fixed

- Admin: fix password recovery success URL
- Picotable: render the filters button on small devices,
  even when there is no data, to allow resetting filters

## [1.10.4] - 2020-02-22

### Changed

- Make Admin messages dismissible

### Fixed

- Admin: Fix search results overflowing the canvas

## [1.10.3] - 2020-02-21

### Fixed

- Admin: fix bug when uploading product media

## [1.10.2] - 2020-02-19

### Added

- Admin: add option to impersonate staff users
- Notify: add option to delete notify scripts
- Admin: Allow shop staff to impersonate regular users
- Notify: Add BCC and CC fields to SendEmail notification action.
- Add the CHANGELOG.md to the root of the code base.

### Changed

- Xtheme: Improve template injection by checking not wasting time invoking regex for nothing
- Add `MiddlewareMixin` to all middlewares to prepare for Django 2.x
- Notify: Changed the Email topology type to support comma-separated list of emails when using constants.
- Front: skip product filter refresh if filters not defined
- GDPR: change "i agree" button to "i understand"

### Fixed

- Front: fix notification template default content
- Admin: improve primary image fallback for product
- Fixed the placeholder of Select2 component in Admin
- FileDnDUploader: Add check for the `data-kind` attribute of the drop zone. If the data-kind is
  `images`, add an attribute to the hidden input that only allows images to be uploaded.
- Front: fix bug with imagelightbox
- CMS: Free page URL on delete

## Older versions

Find older release notes [here](./doc/changelog.rst).
