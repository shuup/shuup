# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
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
#  1. Update the Change Log (ChangeLog.rst)
#      - Make sure all relevant changes since last release are listed
#      - Remove the instruction bullet point ("List all changes after
#        x.x.x here...")
#      - Change the "Unreleased" header to appropriate version header.
#        See header of the last release for example.
#  2. Update VERSION variable here: Increase and drop .post0.dev suffix
#  3. Update version and release variables in doc/conf.py
#  4. Commit changes of steps 1--3
#  5. Tag the commit (of step 4) with
#        git tag -a -m "Shoop X.Y.Z" vX.Y.Z
#     where X.Y.Z is the new version number (must be same as VERSION
#     variable here)
#  6. Check the tag is OK and push it with
#        git push origin refs/tags/vX.Y.Z
#  7. Do a post-release commit:
#      - Add new "Unreleased" header and instruction bullet point to
#        Change Log
#      - Add ".post0.dev" suffix to VERSION variable here

NAME = 'shoop'
VERSION = '1.1.0'
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

utils.set_exclude_patters([
    'build', 'doc',
    'node_modules', 'bower_components',
    'var', '__pycache__', 'LC_MESSAGES',
    '.tox', 'venv*',
    '.git', '.gitignore',
    'local_settings.py',
])

REQUIRES = [
    'Babel==1.3',
    'Django==1.8.2',
    'django-bootstrap3==6.1.0',
    'django-countries==3.3',
    'django-enumfields==0.7.3',
    'django-filer==0.9.11',
    'django-jinja==1.4.1',
    'django-mptt==0.7.4',
    'django-parler==1.4',
    'django-polymorphic==0.7.1',
    'django-registration-redux==1.2',
    'django-timezone-field==1.2',
    'djangorestframework==3.1.3',
    'factory-boy==2.5.2',
    'fake-factory==0.5.2',
    'jsonfield==1.0.3',
    'Markdown==2.6.2',
    'pytz==2015.4',
    'requests==2.7.0',
    'six==1.9.0',
]

REQUIRES_FOR_PYTHON2_ONLY = [
    'enum34==1.0.4',
]

EXTRAS_REQUIRE = {
    ':python_version=="2.7"': REQUIRES_FOR_PYTHON2_ONLY,
    'docs': [
        'Sphinx==1.3.1',
    ],
    'testing': utils.get_test_requirements_from_tox_ini(TOPDIR),
    'coding-style': [
        'flake8==2.4.1',
        'mccabe==0.3.1',
        'pep8==1.5.7',
        'pep8-naming==0.2.2',
        'pyflakes==0.8.1',
    ],
}
EXTRAS_REQUIRE['everything'] = list(set(sum(EXTRAS_REQUIRE.values(), [])))


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
        packages=utils.find_packages(),
        include_package_data=True,
        cmdclass=utils.COMMANDS,
    )
