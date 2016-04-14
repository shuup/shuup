# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import os
import sys

import setuptools

import shoop_setup_utils as utils

TOPDIR = os.path.abspath(os.path.dirname(__file__))
LONG_DESCRIPTION_FILE = os.path.join(TOPDIR, 'README.rst')
VERSION_FILE = os.path.join(TOPDIR, 'shoop', '_version.py')

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
#  5. Commit changes of steps 1--3
#  6. Tag the commit (of step 4) with
#        git tag -a -m "Shoop X.Y.Z" vX.Y.Z
#     where X.Y.Z is the new version number (must be same as VERSION
#     variable here)
#  7. Check the tag is OK and push it with
#        git push origin refs/tags/vX.Y.Z
#  8. Do a post-release commit:
#      - Add new "Unreleased" header and instruction bullet point to
#        Change Log
#      - Add ".post0.dev" suffix to VERSION variable here

NAME = 'shoop'
VERSION = '3.0.0.post0.dev'
DESCRIPTION = 'E-Commerce Platform'
AUTHOR = 'Shoop Ltd.'
AUTHOR_EMAIL = 'shoop@shoop.io'
URL = 'http://shoop.io/'
LICENSE = 'AGPL-3.0'  # https://spdx.org/licenses/
CLASSIFIERS = """
Development Status :: 4 - Beta
Intended Audience :: Developers
License :: OSI Approved :: GNU Affero General Public License v3
Natural Language :: English
Programming Language :: JavaScript
Programming Language :: Python :: 2
Programming Language :: Python :: 2.7
Programming Language :: Python :: 3
Programming Language :: Python :: 3.4
Topic :: Internet :: WWW/HTTP :: Site Management
Topic :: Office/Business
Topic :: Software Development :: Libraries :: Application Frameworks
Topic :: Software Development :: Libraries :: Python Modules
""".strip().splitlines()

EXCLUDED_PACKAGES = [
    'shoop_tests', 'shoop_tests.*',
]

utils.set_exclude_patters([
    '__pycache__', '*.py[cod]',
    'node_modules', 'bower_components',
    'build', 'doc', 'var',
    '.tox', '.cache', 'venv*',
    '.git', '.gitignore',
    'LC_MESSAGES',
    'local_settings.py',
])

REQUIRES = [
    'Babel~=2.2',
    'Django~=1.8.0',
    'django-bootstrap3~=6.1',
    'django-countries~=3.3',
    'django-enumfields~=0.7.2',
    'django-filer~=1.0',
    'django-jinja~=1.4',
    'django-mptt~=0.8.0',
    'django-parler~=1.5',
    'django-parler-rest~=1.3a1',
    'django-polymorphic>=0.8,<0.10',
    # django-registration-redux>=1.4 does not work with
    # our custom get_success_url
    'django-registration-redux~=1.2,<1.4',
    'django-timezone-field~=1.2',

    # djangorestframework>=3.3.0 does not work with
    # django-parler-rest 1.3a1 because compat.OrderedDict was dropped
    'djangorestframework~=3.1,<3.3.0',

    'factory-boy~=2.5',
    'fake-factory~=0.5.0,<0.5.4',
    'Jinja2~=2.8',
    'jsonfield~=1.0',
    'Markdown~=2.6',
    'pytoml~=0.1.0',
    'pytz>=2015.4',
    'requests~=2.7',
    'six~=1.9',
]

REQUIRES_FOR_PYTHON2_ONLY = [
    # enum34 1.1 or newer does not currently work. See
    # https://github.com/hzdg/django-enumfields/pull/44
    'enum34~=1.0,<1.1',
]

EXTRAS_REQUIRE = {
    ':python_version=="2.7"': REQUIRES_FOR_PYTHON2_ONLY,
    'docs': [
        'Sphinx~=1.3',
    ],
    'testing': utils.get_test_requirements_from_tox_ini(TOPDIR),
    'coding-style': [
        'flake8~=2.4',
        'pep8-naming~=0.2',
    ],
}
EXTRAS_REQUIRE['everything'] = list(
    set(sum(EXTRAS_REQUIRE.values(), [])) -  # All extras, but not...
    set(REQUIRES_FOR_PYTHON2_ONLY)  # the Python 2 compatibility things
)


if __name__ == '__main__':
    if 'register' in sys.argv or 'upload' in sys.argv:
        raise EnvironmentError('Registering and uploading is blacklisted')

    version = utils.get_version(VERSION, TOPDIR, VERSION_FILE)
    utils.write_version_to_file(version, VERSION_FILE)

    setuptools.setup(
        name=NAME,
        version=version,
        description=DESCRIPTION,
        long_description=utils.get_long_description(LONG_DESCRIPTION_FILE),
        url=URL,
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
