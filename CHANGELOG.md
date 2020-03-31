# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

List all changes after the last release here (newer on top). Each change on a separate bullet point line.


### Fixed

- Admin: Notification name when deleteing it

### Changed

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
