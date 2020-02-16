# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import os

import setuptools

from . import excludes

if hasattr(setuptools, "PackageFinder"):
    # This only exists in setuptools in versions >= 2014-03-22
    # https://bitbucket.org/pypa/setuptools/commits/09e0ab6bb31c3055a19c856e328ba99e225ab8d7
    class FastFindPackages(setuptools.PackageFinder):
        @staticmethod
        def _candidate_dirs(base_path):
            """
            Return all dirs in base_path that might be packages.

            This overrides the base class method to add filtering
            subdirectories matching excludes out _during_ the search.

            This makes a significant difference on some file systems
            (looking at you, Windows, when `node_modules` exists).
            """
            items = excludes.walk_excl(base_path, followlinks=True)
            for (root, dirs, files) in items:
                dirs[:] = [x for x in dirs if '.' not in x]
                for dir in dirs:
                    yield os.path.relpath(os.path.join(root, dir), base_path)

        @staticmethod
        def _all_dirs(base_path):
            # For setuptools < 18.2
            return FastFindPackages._candidate_dirs(base_path)

    def find_packages(*args, **kwargs):
        kwargs.setdefault('exclude', excludes.get_exclude_patterns())
        return FastFindPackages.find(*args, **kwargs)
else:
    def find_packages(*args, **kwargs):
        kwargs.setdefault('exclude', excludes.get_exclude_patterns())
        return setuptools.find_packages(*args, **kwargs)
