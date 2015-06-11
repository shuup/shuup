# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from fnmatch import fnmatch
import os
import sys

import setuptools


NAME = 'shoop'
DESCRIPTION = 'Web shop'
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

EXCLUDE_PATTERNS = [
    'contrib', 'docs', 'tests*', 'node_modules',
    'bower_components', 'var', '__pycache__', 'LC_MESSAGES',
    'venv*',
]

REQUIRES = [
    'django-parler==1.4',
    'django-polymorphic==0.7.1',
    'Django==1.8.2',
    'jsonfield==1.0.3',
    'six==1.9.0',
    'django-countries==3.3',
    'Babel==1.3',
    'django-enumfields==0.7.3',
    'django-jinja==1.4.1',
    'django-mptt==0.7.3',
    'django-filer==0.9.10',
    'django-timezone-field==1.2',
    'django-bootstrap3==5.4.0',
    'Markdown==2.6.2',
    'pytz==2015.4',
    'requests==2.6.0',
    'factory-boy==2.5.2',
    'fake-factory==0.5.1',
]

REQUIRES_FOR_PYTHON2_ONLY = [
    'enum34==1.0.4',
]

if sys.version_info[0] == 2:
    REQUIRES += REQUIRES_FOR_PYTHON2_ONLY

TESTS_REQUIRE = [
    "beautifulsoup4==4.3.2",
    "mock==1.0.1",
    "pytest-cache==1.0",
    "pytest==2.7.1",
    "pytest-cov==1.8.1",
    'pytest-django==2.8.0',
]

EXTRAS_REQUIRE = {
    'docs': [
        'Sphinx==1.3.1',
    ],
    'testing': TESTS_REQUIRE,
    'shoop.front.apps.registration': [
        'django-registration-redux==1.2',
    ],
    'coding-style': [
        'flake8==2.4.1',
        'mccabe==0.3',
        'pep8==1.5.7',
        'pep8-naming==0.2.2',
        'pyflakes==0.8.1',
    ],
}
EXTRAS_REQUIRE['everything'] = list(set(sum(EXTRAS_REQUIRE.values(), [])))

VERSION_FILE = os.path.join(NAME, 'version.py')
LONG_DESCRIPTION_FILE = None

TOPDIR = os.path.abspath(os.path.dirname(__file__))


def get_version(path=TOPDIR, filename=VERSION_FILE):
    """
    Get version from file.
    """
    with open(os.path.join(path, filename), 'rt') as fp:
        for line in fp:
            if line.startswith("__version__ = '") and line.endswith("'\n"):
                return line.split("'", 1)[-1][:-2]
    return 'unknown'


def get_long_description(path=TOPDIR, filename=LONG_DESCRIPTION_FILE):
    """
    Get long description from file.
    """
    if not filename:
        return None
    with open(os.path.join(path, filename), 'rt') as f:
        return f.read()


if hasattr(setuptools, "PackageFinder"):
    # This only exists in setuptools in versions >= 2014-03-22
    # https://bitbucket.org/pypa/setuptools/commits/09e0ab6bb31c3055a19c856e328ba99e225ab8d7
    class FastFindPackages(setuptools.PackageFinder):
        @staticmethod
        def _all_dirs(base_path):
            """
            Return all dirs in base_path, relative to base_path, but filtering
            subdirectories matching excludes out _during_ the search.

            This makes a significant difference on some file systems
            (looking at you, Windows, when `node_modules` exists).
            """
            def is_excluded_dir(dir):
                return any(fnmatch(dir, pat) for pat in EXCLUDE_PATTERNS)

            for root, dirs, files in os.walk(base_path, followlinks=True):
                dirs[:] = [dir for dir in dirs if not is_excluded_dir(dir)]
                for dir in dirs:
                    yield os.path.relpath(os.path.join(root, dir), base_path)
    find_packages = FastFindPackages.find
else:
    find_packages = setuptools.find_packages


if __name__ == '__main__':
    if 'register' in sys.argv or 'upload' in sys.argv:
        raise EnvironmentError('Registering and uploading is blacklisted')

    setuptools.setup(
        name=NAME,
        version=get_version(),
        description=DESCRIPTION,
        long_description=get_long_description(),
        url=URL,
        author=AUTHOR,
        author_email=AUTHOR_EMAIL,
        license=LICENSE,
        classifiers=CLASSIFIERS,
        install_requires=REQUIRES,
        tests_require=TESTS_REQUIRE,
        extras_require=EXTRAS_REQUIRE,
        packages=find_packages(exclude=EXCLUDE_PATTERNS),
        include_package_data=True,
    )
