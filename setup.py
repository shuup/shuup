# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import os
import sys

import setuptools

import shuup_setup_utils as utils

TOPDIR = os.path.abspath(os.path.dirname(__file__))
LONG_DESCRIPTION_FILE = os.path.join(TOPDIR, 'README.rst')
VERSION_FILE = os.path.join(TOPDIR, 'shuup', '_version.py')

# Release instructions
#
#  1. Update the Change Log (doc/changelog.rst)
#      - Make sure all relevant changes since last release are listed
#      - Remove the instruction bullet point ("List all changes after
#        x.x.x here...")
#      - Change the "Unreleased" header to appropriate version header.
#        See header of the last release for example.
#  2. Create/update Release Notes (doc/release_notes/<VERSION>.rst) and
#     add it to index (doc/release_notes/index.rst)
#  3. Update VERSION variable here: Increase and drop .post0.dev suffix
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

NAME = 'shuup'
VERSION = '1.7.1'
DESCRIPTION = 'E-Commerce Platform'
AUTHOR = 'Shuup Inc.'
AUTHOR_EMAIL = 'shuup@shuup.com'
URL = 'http://shuup.com/'
DOWNLOAD_URL_TEMPLATE = (
    'https://github.com/shuup/shuup/releases/download/'
    'v{version}/shuup-{version}-py2.py3-none-any.whl')
LICENSE = 'proprietary'  # https://spdx.org/licenses/
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
Programming Language :: Python :: 2
Programming Language :: Python :: 2.7
Programming Language :: Python :: 3
Programming Language :: Python :: 3.4
Programming Language :: Python :: 3.5
Programming Language :: Python :: 3.6
Topic :: Internet :: WWW/HTTP :: Dynamic Content
Topic :: Internet :: WWW/HTTP :: Site Management
Topic :: Office/Business
Topic :: Software Development :: Libraries :: Application Frameworks
Topic :: Software Development :: Libraries :: Python Modules
""".strip().splitlines()

EXCLUDED_PACKAGES = [
    'shuup_tests', 'shuup_tests.*',
]

utils.add_exclude_patters([
    'build', 'doc', 'var',
    'LC_MESSAGES',
    'local_settings.py',
])

REQUIRES = [
    'Babel==2.5.3',
    'Django>=1.8,<2',
    'django-bootstrap3>=6.1,<10',
    'django-countries>=3.3,<5.3',
    'django-enumfields>=0.9,<0.10',
    'django-filer>=1.0,<2',
    'django-filter>=1.0,<1.2',
    'django-jinja>=1.4,<3',
    'django-mptt>=0.8.0,<0.10',  # Django-filer doesn't officially support 0.9.0
    'django-parler>=1.5,<2',
    'django-parler-rest>=1.3a1,<2',
    'django-polymorphic>=0.8,<2.1.0',  # For Django 1.8 and 1.9 use version lower 1
    'django-registration-redux>=1.5,<1.9',
    'django-reversion>=2,<3',
    'django-timezone-field>=1.2,<3',
    'djangorestframework>=3.5,<3.6',
    'djangorestframework-jwt>=1.9,<2',
    'django_rest_swagger>=2.1.0,<2.2',
    'factory-boy==2.7.0',
    'fake-factory>=0.5.0,<0.5.4',
    'Jinja2==2.8.1',
    'jsonfield>=1',
    'keyring>=10',
    'keyrings.alt>=2',
    'lxml>=4,<4.2.2',
    'Markdown>=2.6,<3',
    'openpyxl>=2.3',
    'python-dateutil>=2.5',
    'pytoml>=0.1.0,<0.2',
    'pytz>=2015.4',
    'requests>=2.7,<3',
    'secretstorage==2.3.1',
    'six>=1.9,<2',
    'unicodecsv==0.14.1',
    'xlrd>=1'
]

REQUIRES_FOR_PYTHON2_ONLY = [
    'pillow>=3.4.2,<4'
]

EXTRAS_REQUIRE = {
    ':python_version=="2.7"': REQUIRES_FOR_PYTHON2_ONLY,
    'docs': [
        'Sphinx>=1.3,<2',
    ],
    'testing': utils.get_test_requirements_from_tox_ini(TOPDIR),
    'coding-style': [
        'flake8==3.3.0',
        'flake8-isort==2.1.3',
        'flake8-polyfill==1.0.1',
        'isort==4.2.5',
        'pep8-naming==0.4.1'
    ],
}
EXTRAS_REQUIRE['everything'] = list(
    set(sum(EXTRAS_REQUIRE.values(), [])) -  # All extras, but not...
    set(REQUIRES_FOR_PYTHON2_ONLY)  # the Python 2 compatibility things
)


if __name__ == '__main__':
    if 'upload' in sys.argv:
        raise EnvironmentError('Uploading is blacklisted')

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
        tests_require=EXTRAS_REQUIRE['testing'],
        extras_require=EXTRAS_REQUIRE,
        packages=utils.find_packages(exclude=EXCLUDED_PACKAGES),
        include_package_data=True,
        cmdclass=utils.COMMANDS,
    )
