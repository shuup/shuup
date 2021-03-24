#!/usr/bin/env python
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

import os
import subprocess
import sys

APIDOC_EXCLUDES = []


def main():
    os.chdir(os.path.dirname(__file__))
    apidoc_dir = os.path.join("doc", "api")

    # Remove all the previous versions
    for filename in os.listdir(apidoc_dir):
        if filename.endswith(".rst") and filename != "modules.rst":
            os.remove(os.path.join(apidoc_dir, filename))

    # Generate a list of migration dirs to exclude
    migration_excludes = []
    for (root, dirnames, filenames) in os.walk("shuup"):
        if "migrations" in dirnames:
            migration_excludes.append(os.path.join(root, "migrations"))

    # Generate new
    retcode = subprocess.call(
        ["sphinx-apidoc", "-o", "doc/api", "shuup"] + APIDOC_EXCLUDES + migration_excludes + sys.argv
    )
    raise SystemExit(retcode)


if __name__ == "__main__":
    main()
