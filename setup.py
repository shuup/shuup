# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import os
import sys

import setuptools

import shuup_setup_utils as utils

TOPDIR = os.path.abspath(os.path.dirname(__file__))
LONG_DESCRIPTION_FILE = os.path.join(TOPDIR, "README.rst")
VERSION_FILE = os.path.join(TOPDIR, "shuup", "_version.py")

# Release instructions
#
#  1. Update the Change Log (CHANGELOG.md)
#      - Make sure all relevant changes since last release are listed
#      - Remove the instruction bullet point ("List all changes after
#        x.x.x here...")
#      - Change the "Unreleased" header to appropriate version header.
#        See header of the last release for example.
#  2. Update VERSION variable here: Increase and drop .post0.dev suffix
#  4. Update version and release variables in doc/conf.py
#  5. Commit changes of steps 1--4
#  6. Tag the commit (of step 5) with
#        git tag -a -m "Shuup X.Y.Z" vX.Y.Z
#     where X.Y.Z is the new version number (must be same as VERSION
#     variable here)
#  7. Check the tag is OK and push it with
#        git push origin refs/tags/vX.Y.Z
#  8. Do a post-release commit:
#      - Add new "Unreleased" header and instruction bullet point to
#        Change Log
#      - Add ".post0.dev" suffix to VERSION variable here

NAME = "shuup"
VERSION = "2.9.1.post0.dev"
DESCRIPTION = "E-Commerce Platform"
AUTHOR = "Shuup Commerce Inc."
AUTHOR_EMAIL = "shuup@shuup.com"
URL = "http://shuup.com/"
DOWNLOAD_URL_TEMPLATE = (
    "https://github.com/shuup/shuup/releases/download/" "v{version}/shuup-{version}-py2.py3-none-any.whl"
)
LICENSE = "proprietary"  # https://spdx.org/licenses/
CLASSIFIERS = """
Development Status :: 5 - Production/Stable
Intended Audience :: Developers
License :: Other/Proprietary License
Natural Language :: English
Natural Language :: Chinese (Simplified)
Natural Language :: Finnish
Natural Language :: Japanese
Natural Language :: Portuguese (Brazilian)
Programming Language :: JavaScript
Programming Language :: Python :: 3.6
Programming Language :: Python :: 3.7
Programming Language :: Python :: 3.8
Topic :: Internet :: WWW/HTTP :: Dynamic Content
Topic :: Internet :: WWW/HTTP :: Site Management
Topic :: Office/Business
Topic :: Software Development :: Libraries :: Application Frameworks
Topic :: Software Development :: Libraries :: Python Modules
""".strip().splitlines()

EXCLUDED_PACKAGES = [
    "shuup_tests",
    "shuup_tests.*",
]

utils.add_exclude_patters(
    [
        "build",
        "doc",
        "var",
        "LC_MESSAGES",
        "local_settings.py",
    ]
)

# This requires is updated based on the poetry2setup command output
# Use https://pypi.org/project/poetry2setup/ to update it
REQUIRES = [
    "Babel>=2.9.1,<3.0.0",
    "Django>=2.2,<4",
    "Faker>=7,<8",
    "Jinja2<3",
    "Markdown>=3.3.4,<4.0.0",
    "bleach>=3.3.0,<4.0.0",
    "django-bootstrap3>=15.0.0,<16.0.0",
    "django-countries>=7.2.1,<8.0.0",
    "django-enumfields>=2.1.1,<3.0.0",
    "django-filer>=2.0.2,<3.0.0",
    "django-filter>=2.4.0,<3.0.0",
    "django-jinja>=2.7.0,<3.0.0",
    "django-mptt>=0.12.0,<0.13.0",
    "django-parler>=2.2,<3.0",
    "django-polymorphic>=3.0.0,<4.0.0",
    "django-registration-redux>=2.9,<3.0",
    "django-reversion>=3.0.9,<4.0.0",
    "django-timezone-field>=4.1.2,<5.0.0",
    "djangorestframework>=3.12.4,<4.0.0",
    "easy-thumbnails>=2.7.1,<3.0.0",
    "factory-boy>=3.2.0,<4.0.0",
    "jsonfield>=3.1.0,<4.0.0",
    "keyrings.alt>=4.0.2,<5.0.0",
    "lxml>=4.6.3,<5.0.0",
    "openpyxl>=3.0.7,<4.0.0",
    "python-dateutil>=2.8.1,<3.0.0",
    "requests>=2.25.1,<3.0.0",
    "six>=1.16.0,<2.0.0",
    "toml>=0.10.2,<0.11.0",
    "unicodecsv>=0.14.1,<0.15.0",
    "weasyprint>=52.5,<53.0",
    "xlrd>=2.0.1,<3.0.0",
]

if __name__ == "__main__":
    if "upload" in sys.argv:
        raise EnvironmentError("Uploading is blacklisted")

    version = utils.get_version(VERSION, TOPDIR, VERSION_FILE)
    utils.write_version_to_file(version, VERSION_FILE)

    setuptools.setup(
        name=NAME,
        version=version,
        description=DESCRIPTION,
        long_description=utils.get_long_description(LONG_DESCRIPTION_FILE),
        url=URL,
        download_url=DOWNLOAD_URL_TEMPLATE.format(version=version),
        author=AUTHOR,
        author_email=AUTHOR_EMAIL,
        license=LICENSE,
        classifiers=CLASSIFIERS,
        install_requires=REQUIRES,
        python_requires=">=3.6,<4.0",
        packages=utils.find_packages(exclude=EXCLUDED_PACKAGES),
        include_package_data=True,
        cmdclass=utils.COMMANDS,
    )
