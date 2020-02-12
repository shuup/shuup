# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

List all changes after the last release here (newer on top). Each change on a separate bullet point line.

### Added

- Notify: Add BCC and CC fields to SendEmail notification action.
- Add the CHANGELOG.md to the root of the code base.

### Changed

- Xtheme: Improve template injection by checking not wasting time invoking regex for nothing
- Add `MiddlewareMixin` to all middlewares to prepare for Django 2.x
- Notify: Changed the Email topology type to support comma-separated list of emails when using constants.

### Fixed
- FileDnDUploader: Add check for the `data-kind` attribute of the drop zone. If the data-kind is
  `images`, add an attribute to the hidden input that only allows images to be uploaded.

## Older versions

Find older release notes [here](./doc/changelog.rst).
